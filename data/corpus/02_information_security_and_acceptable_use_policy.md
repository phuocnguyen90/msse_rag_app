# Information Security and Acceptable Use Policy

**Document ID:** POL-SEC-2025  
**Effective Date:** February 15, 2025  
**Version:** 4.0  
**Applicability:** All Employees, Contractors, and Third-Party Vendors with access to Apex Technologies Systems.

---

## 1. Objective and Scope
This policy mandates the standard security practices required to safeguard Apex Technologies' digital assets, customer information, source code, and internal computing infrastructure from unauthorized access, loss, or compromise.

---

## 2. Authentication, Passwords, and Multi-Factor Authentication (MFA)
- **Password Length & Complexity:** Passwords must be at least fourteen (14) characters long and incorporate at least one uppercase letter, one lowercase letter, one numeric digit, and one special character (e.g., `!@#$%^&*`).
- **Password Expiration & History:** System passwords expire every ninety (90) days. The reuse of any of the previous twelve (12) passwords is mathematically prohibited by identity directory policies.
- **Mandatory MFA:** Multi-Factor Authentication (MFA) is strictly mandatory across all corporate accounts, VPN gateways, cloud consoles, code repositories, and email inboxes. SMS-based verification is deprecated; employees must utilize hardware security keys (e.g., YubiKey) or time-based one-time password (TOTP) authenticator apps.
- **Credential Sharing:** Sharing credentials, accounts, or API tokens under any circumstances constitutes an immediate gross compliance violation.

---

## 3. Data Classification and Handling Tiers
Apex Technologies categorizes all electronic and physical assets into four distinct sensitivity tiers:

1. **Public (Tier 1):** Marketing collateral, public technical documentation, press releases. No special access controls required.
2. **Internal Business (Tier 2):** General company correspondence, project roadmaps, operational guidelines. Requires corporate domain authentication.
3. **Confidential (Tier 3):** Proprietary source code, customer account metadata, commercial contracts, financial forecasts. Access is restricted on a strict need-to-know basis and requires encryption at rest (AES-256) and in transit (TLS 1.3).
4. **Restricted / PII (Tier 4):** Personally Identifiable Information (PII), employee social security numbers, banking credentials, customer cryptographic keys. Strict role-based access control (RBAC), audit logging, and explicit CISO approval are required for data access.

---

## 4. Workstation Security and Clean Desk Standard
- **Screen Lock Timeout:** All laptops and workstations must be configured to automatically lock displays after five (5) minutes of user inactivity.
- **Manual Locking:** Employees must manually lock their screens (`Win + L` or `Cmd + Ctrl + Q`) whenever stepping away from their work area.
- **Clean Desk Policy:** Sensitive physical papers, access badges, and confidential documents must be locked in designated filing cabinets when unattended.
- **Removable Media & USB Prohibition:** The insertion of non-corporate USB storage drives or external unencrypted hard drives into company hardware is disabled via endpoint protection software.

---

## 5. Network Access, Wi-Fi, and VPN Usage
- **Public Wi-Fi Restrictions:** Employees working from hotels, cafes, airports, or client premises must never transmit company data across unsecured public Wi-Fi networks without an active corporate WireGuard/IPsec VPN tunnel.
- **Remote Desktop & SSH:** Direct exposure of administrative ports (e.g., RDP port 3389, SSH port 22) to the public Internet without VPN or identity-aware proxy traversal is prohibited.

---

## 6. Incident Reporting and SLA
- **Immediate Notification:** Any suspected compromise, phishing engagement, loss of equipment, or unauthorized data disclosure must be reported within two (2) hours of discovery to `security-incident@apextech.internal` or via the emergency Slack channel `#sec-ops`.
- **Whistleblower Protection:** Security disclosures made in good faith will not result in disciplinary action against the reporting employee.
