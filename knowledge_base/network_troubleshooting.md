# Network Troubleshooting Guide - TeleNova

## Understanding Signal and Connectivity

### Signal Strength Indicators
- **4 bars / Full signal**: Excellent connectivity, all services available
- **2–3 bars**: Good connectivity, minor speed reductions possible
- **1 bar**: Weak signal, voice calls may drop, data speeds limited
- **No signal (X)**: Outside coverage area or device issue

### Network Technologies
- **5G**: Available in major metro areas; speeds up to 1 Gbps
- **LTE (4G)**: Nationwide coverage; speeds 10–150 Mbps
- **3G (HSPA+)**: Legacy fallback; speeds 1–10 Mbps
- **2G**: Emergency fallback only; data not recommended

---

## Common Issues and Step-by-Step Fixes

### Issue 1: No Service / No Signal

**Step 1**: Check coverage map
- Visit coverage.telenovaconnect.com or use the TeleNova app
- Enter your location to confirm you're within the coverage area

**Step 2**: Toggle Airplane Mode
- Enable Airplane Mode for 15 seconds, then disable it
- This forces the device to re-register with the nearest tower

**Step 3**: Restart the device
- Power off completely (not just restart)
- Wait 30 seconds, then power back on

**Step 4**: Check SIM card
- Power off device and remove SIM card
- Inspect for damage or debris; clean gently with dry cloth
- Reinsert firmly and power on

**Step 5**: Manual network selection
- Settings → Mobile Network → Network Operators → Search manually
- Select TeleNova from the list

**Step 6**: Contact support if unresolved
- Provide your location (ZIP code or address)
- Include device model and OS version
- Note the time the issue started

---

### Issue 2: Slow Data Speeds

**Step 1**: Run a speed test
- Use Speedtest.net or the TeleNova Speed Check in the app
- Note download/upload speeds and server location

**Step 2**: Check data plan status
- Confirm you haven't exhausted your high-speed data allotment
- After plan limits, speeds reduce to 1 Mbps (data throttling policy)

**Step 3**: Network congestion
- Peak hours (6 PM – 11 PM local) may cause slower speeds in dense areas
- Try again during off-peak hours to confirm

**Step 4**: Clear device cache
- Android: Settings → Storage → Cached Data → Clear
- iOS: Offload unused apps; restart device

**Step 5**: Reset network settings
- **Android**: Settings → General Management → Reset → Reset Network Settings
- **iOS**: Settings → General → Transfer or Reset → Reset → Reset Network Settings
- **Note**: This clears saved Wi-Fi passwords and Bluetooth pairings

**Step 6**: Check for device-side issues
- Test in another location
- Test with a different app to isolate the issue

---

### Issue 3: Calls Dropping or Poor Voice Quality

**Step 1**: Check signal strength in the call area
- Move to an open area or near a window

**Step 2**: Disable Wi-Fi Calling if enabled
- Wi-Fi Calling can conflict with cellular in some configurations
- Settings → Phone → Wi-Fi Calling → Toggle off; retest

**Step 3**: Enable Wi-Fi Calling if experiencing indoor issues
- Indoor cellular signal is often weak; Wi-Fi Calling uses your broadband
- Settings → Phone → Wi-Fi Calling → Toggle on

**Step 4**: Check for VoLTE (Voice over LTE)
- Ensure VoLTE is enabled for HD voice quality
- Settings → Mobile Network → VoLTE → Enable

**Step 5**: Update carrier settings
- iOS: Settings → General → About → "Carrier Settings Update" prompt
- Android: Check for software updates in Settings → Software Update

---

### Issue 4: MMS / Text Messages Not Sending

**Step 1**: Verify MMS settings (APN)
- APN Name: TeleNova
- APN: telenovamms.internet
- MMSC: http://mms.telenovaconnect.com
- MMS Proxy: 192.168.100.1
- MMS Port: 8080

**Step 2**: Ensure mobile data is enabled
- MMS requires a mobile data connection even on unlimited talk/text plans

**Step 3**: Check message size
- MMS limit: 1 MB per message
- Compress images before sending if over the limit

---

### Issue 5: International Roaming Not Working

**Step 1**: Confirm international roaming is enabled on your account
- Log into account.telenovaconnect.com → Plan & Services → International Roaming → Enable
- Activation takes up to 2 hours

**Step 2**: Enable data roaming on device
- iOS: Settings → Cellular → Cellular Data Options → Roaming → Enable Data Roaming
- Android: Settings → Connections → Mobile Networks → Data Roaming → Enable

**Step 3**: Select manual network
- In some countries, automatic network selection fails
- Manually select a partner carrier from the network list

**Supported roaming partners**: 200+ countries. Check roaming.telenovaconnect.com for rates.

---

## Network Outage Information

### How to check for outages
- **App**: Home screen banner will display active outages
- **Web**: status.telenovaconnect.com
- **Twitter/X**: @TeleNovaStatus for real-time updates

### Outage compensation
- Outages exceeding 4 continuous hours qualify for a bill credit
- Credits are automatically applied; no claim needed
- Credit amount: 1 day of service value per qualifying outage

---

## Escalation Criteria for Network Issues

Escalate to Network Engineering if:
- Issue persists after all troubleshooting steps
- Multiple customers in the same area report the same issue
- Issue has lasted more than 24 hours without improvement
- Physical tower damage or infrastructure issue is suspected

---
*Last updated: 2025-Q3 | TeleNova Network Operations*
