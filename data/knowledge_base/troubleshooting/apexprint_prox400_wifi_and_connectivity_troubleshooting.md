# ApexPrint ProX-400 Wi-Fi and Network Connectivity Guide
**Document Type**: Connectivity & Network Administration Guide
**Model**: ProX-400 Series

## 1. Wi-Fi Setup and Connection Troubleshooting
- **WPS Push-Button Setup**: Press the WPS button on your Wi-Fi router. Within 2 minutes, press and hold the Wireless button on the printer control panel for 3 seconds until the Wi-Fi LED begins flashing green. The LED turns solid blue when connected.
- **Manual Wireless Setup Wizard**: On the LCD control panel, navigate to: `Settings` -> `Network Settings` -> `Wireless Setup Wizard`. Select your Network SSID from the detected broadcast list and input the WPA2/WPA3 passphrase using the navigation keypad.
- **Dual-Band Support**: ProX-400 supports both 2.4 GHz (802.11b/g/n) and 5.0 GHz (802.11a/n/ac) bands. Ensure router band steering assigns the printer to a stable frequency.

## 2. Static IP Address Configuration & 802.1x Enterprise Security
- **Static IPv4 Configuration**: Access the printer's Embedded Web Server (EWS) by typing its current DHCP IP address into a web browser, or navigate on the printer display to: `Settings` -> `Network` -> `TCP/IP Configuration` -> `Manual (Static)`.
  - IP Address: e.g., `192.168.1.150`
  - Subnet Mask: `255.255.255.0`
  - Gateway: `192.168.1.1`
  - Primary DNS: `8.8.8.8` (or internal company DNS server).
- **Enterprise 802.1x Network Security**: ProX-400 natively supports 802.1x EAP-TLS and PEAP authentication for enterprise networks without requiring additional software downloads. Configuring 802.1x authentication adheres strictly to enterprise guidelines and does NOT void the warranty or service agreements.
- **Network Adapter Factory Reset**: To reset network adapter to factory defaults, press and hold the `Go` and `Cancel` buttons simultaneously for 10 seconds while powering on until the network status LED blinks orange three times.
