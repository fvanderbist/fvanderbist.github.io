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
        "-srcalias", "myalias",  # <-- Ajout clé ici
        "-alias", "myalias",     # <-- Optionnel, permet de renommer dans le .jks
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
    print("=== Multi-alias Certificate Chain + Key to Keystore Tool ===")

    # Renseigner les alias et leurs fichiers
    entries = [
        {
            "alias": "file",
            "cert_path": "nglmks_file.pem",
            "key_path": "nglmks_file.pkey"
        },
        {
            "alias": "kafka",
            "cert_path": "nglmks_kafka.pem",
            "key_path": "nglmks_kafka.pkey"
        },
    ]

    password = getpass.getpass("Enter a password for the PKCS#12 and JKS keystores - must be at least 6 characters: ").strip()
    if not password or len(password) < 6:
        print("[!] Password must be at least 6 characters.")
        sys.exit(1)

    keystore_file = "multi-keystore.jks"
    if os.path.exists(keystore_file):
        os.remove(keystore_file)

    for entry in entries:
        alias = entry["alias"]
        cert_path = entry["cert_path"]
        key_path = entry["key_path"]

        print(f"\n=== Processing alias: {alias} ===")

        if not os.path.exists(cert_path):
            print(f"[!] File not found: {cert_path}")
            sys.exit(1)
        if not os.path.exists(key_path):
            print(f"[!] File not found: {key_path}")
            sys.exit(1)

        reordered_chain = reorder_chain(cert_path, key_path)

        # Change export_to_p12 to accept alias and output name
        p12_filename = f"{alias}.p12"
        run_cmd([
            "openssl", "pkcs12", "-export",
            "-out", p12_filename,
            "-inkey", key_path,
            "-in", reordered_chain,
            "-passout", f"pass:{password}",
            "-name", alias
        ])
        print(f"[+] Exported {alias} to PKCS#12: {p12_filename}")

        # Import in JKS (append to existing or create first one)
        keytool_cmd = [
            "keytool", "-importkeystore",
            "-srckeystore", p12_filename,
            "-srcstoretype", "PKCS12",
            "-destkeystore", keystore_file,
            "-deststoretype", "JKS",
            "-srcstorepass", password,
            "-deststorepass", password,
            "-srcalias", alias,
            "-alias", alias,
            "-noprompt"
        ]
        run_cmd(keytool_cmd)
        print(f"[+] Imported {alias} into JKS: {keystore_file}")

    print("\n[*] Base64-encoded keystore (JKS):")
    encode_keystore(keystore_file)


if __name__ == "__main__":
    main()