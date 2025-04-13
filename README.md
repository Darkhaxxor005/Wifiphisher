# ☠️ Wifiphisher

**Wifiphisher** is a powerful automated tool for launching **captive portal phishing attacks** to trick users into entering their credentials across a variety of popular platforms — while also supporting **deauthentication attacks** to aid in phishing execution.

> ⚠️ This tool is intended for **educational** and **authorized penetration testing** purposes **only**. Do not use it on networks or systems you do not own or have explicit permission to test.

---

## 🎯 Features

- ✅ Captive Portal Phishing
- ✅ Deauthentication Attack
- ✅ Combined Deauth + Phishing Workflow
- ✅ Host Fake Login Pages for 30+ Popular Platforms
- ✅ Update Check
- ✅ Clean Console Output & Simplified Usage

---

## 🌐 Supported Phishing Templates

The tool includes realistic phishing pages for the following services:

1. Adobe  
2. Badoo  
3. Discord  
4. Dropbox  
5. Ebay  
6. Facebook  
7. Facebook Advanced  
8. Facebook Messenger  
9. Facebook Security  
10. Google  
11. Google (New)  
12. Instagram  
13. Instagram Followers  
14. LinkedIn  
15. Mediafire  
16. Microsoft  
17. Netflix  
18. Origin  
19. PayPal  
20. Pinterest  
21. PlayStation  
22. ProtonMail  
23. Reddit  
24. Roblox  
25. Snapchat  
26. Spotify  
27. Stack Overflow  
28. Steam  
29. TikTok Likes  
30. Twitch  
31. VK  
32. VK Poll  
33. WordPress  

---

## ⚙️ Requirements

- ✅ At least **one** Wi-Fi adapter with **AP mode** support for **captive portal phishing** functionality.
- ✅ **Two** Wi-Fi adapters, one **Monitor mode supported** and one **AP mode suppported**, required to run both **deauthentication** and **captive portal phishing** simultaneously.
- 💻 Python.
- 📡 Linux environment with support for wireless injections (Kali Linux recommended).

---

## 🚀 Usage

### 🔐 Captive Portal Phishing Only
> **sudo python wifiphisher.py**

### 📡 Deauthentication Attack Only
> **sudo python wifiphisher.py --run-deauth**

### 🔥 Combined Phishing + Deauth Attack
> **sudo python wifiphisher.py --deauth**

> Make sure you have **two Wi-Fi adapters** connected for combined mode.

### ✅ Update Command 
> **python wifiphisher.py --update** 

---

## 📌 Disclaimer

Wifiphisher is created for **educational and research** purposes. The author does not hold any responsibility for misuse or damage caused by this tool. Always get proper authorization before testing.

---

## 🤝 Contributing

We welcome all contributions!  
Feel free to fork this repository, improve the code, and submit a **pull request**. Let's make WiFi phishing simulation better together!

---

## 🧠 Signature Line

> **"Think Before You Connect."**
