import os
import sys
import base64
import tempfile
import getpass
import subprocess


def run_cmd(cmd_list, input_data=None):
    print(f"[DEBUG] Running command: {' '.join(cmd_list)}")
    result = subprocess.run(cmd_list, input=input_data, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Error running: {' '.join(cmd_list)}")
        print("[STDOUT]")
        print(result.stdout)
        print("[STDERR]")
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def reorder_chain(chain_file, key_file):
    print("[*] Parsing and reordering the certificate chain...")

    with open(chain_file, 'r') as f:
        content = f.read()

    certs = content.strip().split("-----END CERTIFICATE-----")
    certs = [c + "-----END CERTIFICATE-----\n" for c in certs if "-----BEGIN CERTIFICATE-----" in c]

    cert_data = []
    for cert in certs:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(cert.encode())
        temp.close()

        subject = run_cmd(["openssl", "x509", "-in", temp.name, "-noout", "-subject", "-nameopt", "RFC2253"]).strip().replace("subject=", "")
        issuer = run_cmd(["openssl", "x509", "-in", temp.name, "-noout", "-issuer", "-nameopt", "RFC2253"]).strip().replace("issuer=", "")
        cert_data.append({
            "path": temp.name,
            "cert": cert,
            "subject": subject,
            "issuer": issuer
        })

    print("[*] Finding the certificate matching the private key...")

    key_modulus = run_cmd(["openssl", "rsa", "-in", key_file, "-noout", "-modulus"]).strip().split('=')[-1]
    leaf = None
    for c in cert_data:
        cert_modulus = run_cmd(["openssl", "x509", "-in", c['path'], "-noout", "-modulus"]).strip().split('=')[-1]
        if cert_modulus == key_modulus:
            leaf = c
            break

    if not leaf:
        print("[!] Could not find a certificate matching the private key.")
        sys.exit(1)

    ordered = [leaf]
    current = leaf
    while True:
        next_cert = next((c for c in cert_data if c["subject"] == current["issuer"] and c not in ordered), None)
        if not next_cert:
            break
        ordered.append(next_cert)
        current = next_cert

    unused = [c for c in cert_data if c not in ordered]
    if unused:
        print("[!] Warning: Some certificates could not be linked. Including them at the end.")
        for c in unused:
            print(f" - Unlinked cert: subject={c['subject']}, issuer={c['issuer']}")
        ordered += unused

    output_path = "cert_reordered.pem"
    with open(output_path, 'w') as f:
        for c in ordered:
            f.write(c["cert"])
    print(f"[+] Chain reordered. Saved to: {output_path}")
    return output_path


def export_to_p12(key_file, cert_file, password):
    print("[*] Exporting to PKCS#12 format...")
    output_p12 = "mycertificate.p12"
    run_cmd([
        "openssl", "pkcs12", "-export",
        "-out", output_p12,
        "-inkey", key_file,
        "-in", cert_file,
        "-passout", f"pass:{password}",
        "-name", "ibm"
    ])
    print(f"[+] Exported to PKCS#12: {output_p12}")
    return output_p12

def create_jks(p12_file, password):
    print("[*] Creating JKS keystore...")
    keystore_file = "mykeystore.jks"
    if os.path.exists("mykeystore.jks"):
        os.remove("mykeystore.jks")
    run_cmd([
        "keytool", "-importkeystore",
        "-srckeystore", p12_file,
        "-srcstoretype", "PKCS12",
        "-destkeystore", keystore_file,
        "-deststoretype", "JKS",
        "-srcstorepass", password,
        "-deststorepass", password,
        "-srcalias", "ibm",  # <-- Ajout clé ici
        "-alias", "ibm",     # <-- Optionnel, permet de renommer dans le .jks
        "-noprompt"
    ])
    print(f"[+] Keystore created: {keystore_file}")
    return keystore_file

def encode_keystore(file_path):
    print(f"[*] Encoding {file_path} in base64...")
    with open(file_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode()
    print(f"[+] Base64-encoded {file_path}:\n")
    print(encoded)


def main():
    print("=== Certificate Chain + Key to Keystore Tool ===")
    cert_path = input("Enter the path to the certificate chain file (.pem): ").strip()
    key_path = input("Enter the path to the private key file (.key): ").strip()
    password = getpass.getpass("Enter a password for the PKCS#12 and JKS keystores - must be at least 6 characters: ").strip()

    if not password or len(password) < 6:
        print("[!] Password must be at least 6 characters.")
        sys.exit(1)

    print(f"[DEBUG] Using password: {password}")

    if not os.path.exists(cert_path):
        print(f"[!] File not found: {cert_path}")
        sys.exit(1)
    if not os.path.exists(key_path):
        print(f"[!] File not found: {key_path}")
        sys.exit(1)

    reordered_chain = reorder_chain(cert_path, key_path)
    p12_file = export_to_p12(key_path, reordered_chain, password)
    jks_file = create_jks(p12_file, password)

    print("\n[*] Base64-encoded keystore (JKS):")
    encode_keystore(jks_file)
    print("\n[*] Base64-encoded keystore (P12):")
    encode_keystore(p12_file)


if __name__ == "__main__":
    main()