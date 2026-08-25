import os
import re
import requests
import base64
from pathlib import Path

def main():
    # Environment variables provided by GitHub Actions
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    issue_number = os.getenv("GITHUB_EVENT_ISSUE_NUMBER")
    
    if not all([token, repo, issue_number]):
        print("Missing required environment variables.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # 1. Fetch issue data
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    print(f"Fetching issue {issue_number} from {url}...")
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    issue_data = res.json()
    body = issue_data["body"]
    print("Successfully fetched issue body.")

    # 2. Parse the structured form data
    # GitHub Issue Forms render submitted fields as markdown headers, e.g.:
    #
    #   ### Full Name
    #
    #   Jane Doe
    #
    #   ### Role
    #
    #   Post-doc
    #
    # So we match on "### Label" and capture everything up to the next
    # "### " header (or end of body), NOT "Label: value" pairs.
    data = {}
    fields = {
        "Full Name": "name",
        "Role": "role",
        "Year Joined": "year",
        "Short Description": "description",
        "Photo drop": "photo_area",
    }

    print("Parsing issue body...")
    for label, key in fields.items():
        pattern = rf"###\s*{re.escape(label)}\s*\n+(.*?)(?=\n###\s|\Z)"
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            data[key] = val
            print(f"  Found {label}: {val[:50]}...")
        else:
            print(f"  Warning: Could not find {label}")

    if "name" not in data or "role" not in data:
        print("Error: Required fields (Name/Role) missing from issue body.")
        print("Full body received:\n", body)
        return

    # 3. Create the slugified folder name
    name_parts = data["name"].split()
    first = name_parts[0].lower()
    last = name_parts[-1].lower()
    # Basic slugify: remove non-alphanumeric
    def slug(s): return re.sub(r'[^a-z0-9]', '', s)
    folder_name = f"{slug(last)}-{slug(first)}"
    
    current_members_root = Path("people/current-members").resolve()
    member_dir = (current_members_root / folder_name).resolve()

    # Safety check: make sure the resolved path is actually a direct child of
    # people/current-members. This guards against a crafted/unexpected name
    # (e.g. containing "..") escaping the intended directory and touching
    # unrelated files elsewhere in the repo.
    if member_dir.parent != current_members_root:
        print(
            f"Error: computed member directory {member_dir} is not a direct "
            f"child of {current_members_root}. Aborting."
        )
        return

    member_dir.mkdir(parents=True, exist_ok=True)

    # 4. Create description.txt
    desc_lines = [
        f"Name: {data['name']}",
        f"Role: {data['role']}"
    ]
    if data.get("year"):
        desc_lines.append(f"Year: {data['year']}")
    desc_lines.append(f"Description: {data['description']}")
    
    (member_dir / "description.txt").write_text("\n".join(desc_lines), encoding="utf-8")

    # 5. Handle the Image (Avatar)
    # We look for image attachments in the issue body. GitHub may render a
    # dropped image as markdown (![alt](url)) or, for larger images, as an
    # HTML <img ... src="url"> tag. Check both, preferring the "Photo drop"
    # field's captured text but falling back to the whole body.
    md_img_pattern = r'!\[.*?\]\((https://\S+?\.(?:jpg|jpeg|png|webp))\)'
    html_img_pattern = r'<img\b[^>]*?\bsrc=["\'](https://[^"\']+?)["\'][^>]*?>'

    def find_image_url(text):
        match = re.search(md_img_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(html_img_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    search_text = data.get("photo_area") or body
    img_url = find_image_url(search_text)
    if not img_url and search_text is not body:
        img_url = find_image_url(body)

    if img_url:
        img_res = requests.get(img_url)
        img_res.raise_for_status()
        (member_dir / "avatar.jpeg").write_bytes(img_res.content)
        print(f"Downloaded avatar from {img_url}")
    else:
        print("Warning: No profile photo found in issue body. Creating placeholder.")
        (member_dir / "avatar.jpeg").write_text("placeholder")

    print(f"Successfully created profile for {data['name']} at {member_dir}")

if __name__ == "__main__":
    main()
