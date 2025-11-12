import subprocess
import base64
import os
import sys
import getpass

def create_truststore(cert_file_path, alias, storepass, output_path="truststore.jks"):
    if not os.path.isfile(cert_file_path):
        print(f"❌ Certificate file not found: {cert_file_path}")
        sys.exit(1)

    if os.path.exists(output_path):
        os.remove(output_path)

    try:
        subprocess.run([
            "keytool",
            "-import",
            "-alias", alias,
            "-file", cert_file_path,
            "-keystore", output_path,
            "-storepass", storepass,
            "-noprompt"
        ], check=True)

        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        base64_file = output_path + ".b64"
        with open(base64_file, "w") as b64f:
            b64f.write(encoded)

        print(f"\n✅ Truststore created: {output_path}")
        print(f"📦 Base64 output saved to: {base64_file}")

    except subprocess.CalledProcessError as e:
        print("❌ keytool failed:", e)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ keytool not found. Make sure Java is installed and keytool is in your PATH.")
        sys.exit(1)

if __name__ == "__main__":
    cert_file = input("📍 Enter the path to the PEM certificate file: ").strip()
    alias = input("🔖 Enter the alias to use in the truststore: ").strip()
    output_path = input("🏷️  Enter output JKS filename [default: truststore.jks]: ").strip()
    if not output_path:
        output_path = "truststore.jks"
    password = getpass.getpass("🔐 Enter truststore password: ")

    create_truststore(cert_file, alias, password, output_path)