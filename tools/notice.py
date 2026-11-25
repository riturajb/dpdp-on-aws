"""Put the privacy notice together, check it against the register and Rule 3, and publish it.

  python tools/notice.py check                              # the notice meets Rule 3
  python tools/notice.py show --language en                 # read it, in English
  python tools/notice.py show --language hi                 # ... or in Hindi
  python tools/notice.py publish --profile dpdp-workload-eng   # make it the current notice

What:        Puts the notice together from two sources: the wording, written by people (the
             connecting sentences below, and each purpose's text in the register), and the
             itemised lists, taken from register/personal-data-register.yaml. Every
             purpose that relies on consent becomes a separate choice, with the data it uses
             (itemised), what it makes possible, and who receives the data; purposes under
             Section 7 are listed as such; then how to withdraw, the person's rights, how to
             complain to the Data Protection Board, and whom to contact. The same content is
             written in English and in Hindi.
             The notice gets a version name from its own content (N- and 12 characters of its
             SHA-256 fingerprint), so the version a person saw always means one exact text.
Why:         DPDP Act, Section 5(1) and Rule 3: a notice with or before every request for
             consent, understandable on its own, with an itemised description of the data, the
             purposes, the goods or services they enable, and the links to withdraw, exercise
             rights and complain. Section 5(3) and 6(3): English or a language of the Eighth
             Schedule. The check refuses to publish a notice whose choices differ from the
             register, so the notice cannot offer or leave out a purpose the company records.
             The wording itself is approved by people (Privacy Lead, General Counsel), on the
             notice as a customer reads it (show), not entry by entry.
Who runs it: check and show: anyone, offline. publish: an engineer (PlatformEngineer).
When:        Release 4, Steps 2 and 4; again after every change to the register that changes
             the notice. Test T16 runs the check.
Reads:       The register.   Writes: nothing on the laptop.
Changes AWS: publish only: writes the notice files to the notices bucket
             (dpdp-notices-<account id>) and points notices/current.json at the new version.
             The bucket is locked (Object Lock), so a published version can never be changed
             or removed; a new notice is always a new version. Running it twice is safe.

Not in this release: notice and consent for children's accounts (Release 6), and languages
other than English and Hindi (adding one is a register change; see the Release 4 guide).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "consent"))

import consent_rules as rules  # noqa: E402
from tools import register  # noqa: E402

REGION = "ap-south-1"

# The fixed wording of the notice, in each language. The facts (data, purposes, vendors,
# links) come from the register; only the connecting sentences are here. Every language has
# the same keys; check() reports a missing one.
TEXT = {
    "en": {
        "title": "Privacy notice",
        "intro": ("This notice tells you what personal data we would like to use, why, and what "
                  "you can do. It is complete on its own: you do not need any other document to "
                  "understand it."),
        "choices": "What we ask your consent for",
        "choices_intro": ("Each purpose below is a separate choice. You can agree to some and not "
                          "to others. No choice is ticked in advance."),
        "data": "Data", "enables": "This enables", "shared": "Shared with",
        "nobody": "nobody outside the company",
        "not_consent": "What we use without asking for your consent",
        "s7(a)": ("Section 7(a) of the Digital Personal Data Protection Act, 2023: you gave us "
                  "this information yourself, for this purpose."),
        "records": "Records of this notice and your choices",
        "records_text": ("When you agree, we keep a record of this notice and of your choice. It "
                         "lets us show you, or the Data Protection Board of India, what you agreed "
                         "to. It is part of each consent, not a separate choice."),
        "withdraw": "Withdrawing your consent",
        "withdraw_text": ("You can withdraw any consent at any time, as easily as you gave it: in "
                          "the app under {app_path}, or at {withdraw}."),
        "rights": "Your rights",
        "rights_text": ("You can ask for a summary of your personal data; ask us to correct, "
                        "complete, update or erase it; raise a grievance with us; and nominate "
                        "someone to act for you: {rights}"),
        "complaint": "Complaints to the Data Protection Board of India",
        "complaint_text": ("If you are not satisfied with our answer to your grievance, you can "
                           "complain to the Data Protection Board of India. How to do it: "
                           "{complaint}"),
        "contact": "Contact",
        "contact_text": "{role}: {web_form}, or write to {postal}.",
        "language": "Language",
        "language_text": ("You can read this notice in English or Hindi. For another language of "
                          "the Eighth Schedule to the Constitution, contact the {role}."),
        "India": "India", "Ireland": "Ireland",
    },
    "hi": {
        "title": "गोपनीयता सूचना",
        "intro": ("यह सूचना बताती है कि हम आपके किस व्यक्तिगत डेटा का उपयोग करना चाहते हैं, क्यों, "
                  "और आप क्या कर सकते हैं। यह अपने आप में पूर्ण है: इसे समझने के लिए आपको किसी अन्य "
                  "दस्तावेज़ की आवश्यकता नहीं है।"),
        "choices": "जिनके लिए हम आपकी सहमति मांगते हैं",
        "choices_intro": ("नीचे दिया गया प्रत्येक उद्देश्य एक अलग विकल्प है। आप कुछ के लिए सहमति दे "
                          "सकते हैं और दूसरों के लिए नहीं। कोई भी विकल्प पहले से चुना हुआ नहीं है।"),
        "data": "डेटा", "enables": "इससे संभव होता है", "shared": "किसके साथ साझा",
        "nobody": "कंपनी के बाहर किसी के साथ नहीं",
        "not_consent": "जिनका उपयोग हम आपकी सहमति मांगे बिना करते हैं",
        "s7(a)": ("डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम, 2023 की धारा 7(क): आपने यह जानकारी इसी "
                  "उद्देश्य के लिए स्वयं हमें दी है।"),
        "records": "इस सूचना और आपके विकल्पों का रिकॉर्ड",
        "records_text": ("जब आप सहमति देते हैं, तो हम इस सूचना और आपके विकल्प का रिकॉर्ड रखते हैं। "
                         "इससे हम आपको, या भारतीय डेटा संरक्षण बोर्ड को, दिखा सकते हैं कि आपने किस "
                         "बात के लिए सहमति दी थी। यह प्रत्येक सहमति का हिस्सा है, कोई अलग विकल्प नहीं।"),
        "withdraw": "अपनी सहमति वापस लेना",
        "withdraw_text": ("आप किसी भी सहमति को किसी भी समय उतनी ही आसानी से वापस ले सकते हैं जितनी "
                          "आसानी से आपने उसे दी थी: ऐप में {app_path} में, या {withdraw} पर।"),
        "rights": "आपके अधिकार",
        "rights_text": ("आप अपने व्यक्तिगत डेटा का सारांश मांग सकते हैं; उसे सुधारने, पूरा करने, अद्यतन "
                        "करने या मिटाने के लिए कह सकते हैं; हमारे पास शिकायत दर्ज कर सकते हैं; और अपनी "
                        "ओर से कार्य करने के लिए किसी व्यक्ति को नामित कर सकते हैं: {rights}"),
        "complaint": "भारतीय डेटा संरक्षण बोर्ड से शिकायत",
        "complaint_text": ("यदि आप अपनी शिकायत पर हमारे उत्तर से संतुष्ट नहीं हैं, तो आप भारतीय डेटा "
                           "संरक्षण बोर्ड से शिकायत कर सकते हैं। इसका तरीका: {complaint}"),
        "contact": "संपर्क",
        "contact_text": "{role}: {web_form}, या लिखें: {postal}",
        "language": "भाषा",
        "language_text": ("आप यह सूचना अंग्रेज़ी या हिन्दी में पढ़ सकते हैं। संविधान की आठवीं अनुसूची "
                          "की किसी अन्य भाषा के लिए {role} से संपर्क करें।"),
        "India": "भारत", "Ireland": "आयरलैंड",
    },
}

# Words that would make the notice depend on another document (Rule 3(a)).
OUTSIDE_REFERENCES = ("privacy policy", "terms and conditions", "terms of use")


# ---------------------------------------------------------------- build

def _lang_text(item: dict, key: str, lang: str) -> str:
    """The register's text for one language: key for English, key_hi for Hindi."""
    return str(item.get(key if lang == "en" else f"{key}_{lang}", "") or "").strip()


def build(reg: dict) -> dict:
    """The notice content: the wording, with the lists from the register. Its fingerprint
    gives the version name.

    Three groups of purposes:
      choices             legal basis consent, asked one by one (Section 6(1))
      not_consent         a clause of Section 7: told, not asked
      with_each_consent   recorded as part of each consent (separate_choice: false)
    Children's categories are left out: their notice and consent come in Release 6."""
    langs = reg["notice"]["languages"]
    vendors = {v["id"]: v for v in reg["vendors"]}
    notice = {
        "schema": 1,
        "company": {lang: _lang_text(reg, "company", lang) for lang in langs},
        "languages": langs,
        "contact": reg["notice"]["contact"],
        "links": reg["notice"]["links"],
        "choices": [], "not_consent": [], "with_each_consent": [],
    }
    for c in reg["data_categories"]:
        if c.get("children"):
            continue
        for p in c["purposes"]:
            entry = {
                "purpose_id": p.get("id", ""),
                "category_id": c["id"],
                "fields": list(c["fields"]),
                "data": {lang: _lang_text(c, "notice_description", lang) for lang in langs},
                "purpose": {lang: _lang_text(p, "purpose", lang) for lang in langs},
                "enables": {lang: _lang_text(p, "enables", lang) for lang in langs},
                "shared_with": [{"name": {lang: _lang_text(vendors[v], "name", lang)
                                          for lang in langs},
                                 "location": vendors[v]["location"]}
                                for v in p.get("shared_with") or []],
            }
            if p.get("legal_basis") != "consent":
                entry["basis"] = p.get("legal_basis")
                notice["not_consent"].append(entry)
            elif p.get("separate_choice") is False:
                notice["with_each_consent"].append(entry)
            else:
                notice["choices"].append(entry)
    notice["texts"] = {lang: render(notice, lang) for lang in langs}
    return notice


def render(notice: dict, lang: str) -> str:
    """The notice as the person reads it, in one language: plain text, short sections."""
    t = TEXT[lang]
    links = dict(notice["links"])
    links["app_path"] = links.get("app_path_hi" if lang == "hi" else "app_path", "")
    contact = notice["contact"]
    role = contact["role_hi"] if lang == "hi" else contact["role"]
    postal = contact["postal_hi"] if lang == "hi" else contact["postal"]

    def where(v):
        return f"{v['name'][lang]} ({t.get(v['location'], v['location'])})"

    out = [f"{notice['company'][lang]}", t["title"], "", t["intro"], "",
           t["choices"], t["choices_intro"], ""]
    for i, ch in enumerate(notice["choices"], start=1):
        shared = ", ".join(where(v) for v in ch["shared_with"]) or t["nobody"]
        out += [f"{i}. {ch['purpose'][lang]}",
                f"   {t['data']}: {ch['data'][lang]}",
                f"   {t['enables']}: {ch['enables'][lang]}",
                f"   {t['shared']}: {shared}", ""]
    if notice["not_consent"]:
        out += [t["not_consent"]]
        for p in notice["not_consent"]:
            out += [f"- {p['purpose'][lang]}",
                    f"  {t['data']}: {p['data'][lang]}",
                    f"  {t.get(p['basis'], p['basis'])}"]
        out.append("")
    out += [t["records"], t["records_text"], ""]
    for p in notice["with_each_consent"]:
        out += [f"  {t['data']}: {p['data'][lang]}", ""]
    out += [t["withdraw"], t["withdraw_text"].format(**links), "",
            t["rights"], t["rights_text"].format(**links), "",
            t["complaint"], t["complaint_text"].format(**links), "",
            t["contact"], t["contact_text"].format(role=role, web_form=contact["web_form"],
                                                   postal=postal), "",
            t["language"], t["language_text"].format(role=role)]
    return "\n".join(out) + "\n"


def version(notice: dict) -> str:
    """N- and the first 12 characters of the notice's SHA-256 fingerprint."""
    return rules.notice_version(notice)


# ---------------------------------------------------------------- check

def check(reg: dict, notice: dict) -> list[str]:
    """Every element Rule 3 and Sections 5 and 6 ask of the notice, in every language.
    Returns one line per problem, each starting with its provision; an empty list is a pass."""
    out: list[str] = []
    langs = notice["languages"]

    # Section 5(3) and 6(3): English, and at least one language of the Eighth Schedule.
    if "en" not in langs or len(langs) < 2:
        out.append("[s.5(3)] The notice must be available in English and at least one language "
                   "of the Eighth Schedule.")
    for lang in langs:
        if lang not in TEXT:
            out.append(f"[s.5(3)] No wording for language '{lang}' in tools/notice.py.")
            continue
        missing = sorted(set(TEXT["en"]) - set(TEXT[lang]))
        if missing:
            out.append(f"[s.5(3)] Language '{lang}' lacks: {', '.join(missing)}.")

    # Section 6(1): every purpose that relies on consent is a choice, each with a unique id.
    expected = {p.get("id") for c in reg["data_categories"] if not c.get("children")
                for p in c["purposes"] if p.get("legal_basis") == "consent"
                and p.get("separate_choice") is not False}
    offered = [ch["purpose_id"] for ch in notice["choices"]]
    if not all(offered) or len(offered) != len(set(offered)):
        out.append("[s.6(1)] Every consent purpose needs its own unique id in the register.")
    if set(offered) != expected:
        out.append(f"[s.6(1)] Choices differ from the register: {sorted(set(offered) ^ expected)}")
    all_ids = [p.get("id") for c in reg["data_categories"] for p in c["purposes"]]
    if len(all_ids) != len(set(all_ids)):
        out.append("[s.6(1)] A purpose id is used twice in the register.")

    # Rule 3(b): itemised data, the purpose, and the goods or services it enables, per language.
    for group in ("choices", "not_consent", "with_each_consent"):
        for p in notice[group]:
            for lang in langs:
                for key, rule in (("data", "Rule 3(b)(i)"), ("purpose", "Rule 3(b)(ii)"),
                                  ("enables", "Rule 3(b)(ii)")):
                    if not p[key].get(lang):
                        out.append(f"[{rule}] Purpose '{p['purpose_id']}' has no {key} text in "
                                   f"'{lang}'.")
            for v in p["shared_with"]:
                for lang in langs:
                    if not v["name"].get(lang):
                        out.append(f"[Rule 3(b)] A vendor of '{p['purpose_id']}' has no name in "
                                   f"'{lang}'.")

    # Rule 3(c): the links to withdraw, to exercise rights and to complain to the Board.
    # Section 6(3): the contact who answers questions about processing.
    links = notice["links"]
    for key, rule in (("withdraw", "Rule 3(c)(i)"), ("rights", "Rule 3(c)(ii)"),
                      ("complaint", "Rule 3(c)(iii)")):
        if not str(links.get(key, "")).startswith("https://"):
            out.append(f"[{rule}] No https link for '{key}'.")
    contact = notice["contact"]
    if not contact.get("role") or not (contact.get("web_form") or contact.get("postal")):
        out.append("[s.6(3)] No contact who can answer questions about processing.")

    # Rule 3(a): the text in each language is complete on its own: it contains every link and
    # every choice, and does not send the reader to another document.
    for lang in langs:
        text = notice["texts"].get(lang, "")
        for key in ("withdraw", "rights", "complaint"):
            if links.get(key) and links[key] not in text:
                out.append(f"[Rule 3(c)] The '{lang}' text does not show the '{key}' link.")
        for ch in notice["choices"]:
            if ch["purpose"].get(lang) and ch["purpose"][lang] not in text:
                out.append(f"[Rule 3(b)] The '{lang}' text misses '{ch['purpose_id']}'.")
        low = text.lower()
        for phrase in OUTSIDE_REFERENCES:
            if phrase in low:
                out.append(f"[Rule 3(a)] The '{lang}' text refers to another document "
                           f"('{phrase}').")
    return out


# ---------------------------------------------------------------- publish

def notices_bucket(account: str) -> str:
    """The bucket created by terraform/modules/consent-service."""
    return f"dpdp-notices-{account}"


def publish(session, notice: dict) -> tuple[str, bool]:
    """Write the notice to the notices bucket and make it current.

    Returns (version, changed). Every write sends a SHA-256 checksum, which S3 requires for
    Object Lock buckets. A version already published is never written again: its files are
    locked, and writing them again would only add identical copies."""
    s3 = session.client("s3")
    account = session.client("sts").get_caller_identity()["Account"]
    bucket = notices_bucket(account)
    ver = version(notice)
    sha = rules.fingerprint(notice)

    def put(key, body, ctype):
        s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=ctype,
                      ChecksumAlgorithm="SHA256")

    try:
        s3.head_object(Bucket=bucket, Key=f"notices/{ver}/notice.json")
        exists = True
    except s3.exceptions.ClientError:
        exists = False
    if not exists:
        put(f"notices/{ver}/notice.json", rules.canonical(notice), "application/json")
        for lang, text in notice["texts"].items():
            put(f"notices/{ver}/notice.{lang}.txt", text.encode("utf-8"),
                "text/plain; charset=utf-8")

    try:
        cur = json.loads(s3.get_object(Bucket=bucket, Key="notices/current.json")["Body"].read())
    except s3.exceptions.NoSuchKey:
        cur = {}
    if cur.get("version") == ver:
        return ver, False
    now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")
    put("notices/current.json", json.dumps({"version": ver, "sha256": sha, "published_at": now,
                                            "previous": cur.get("version")}).encode(),
        "application/json")
    return ver, True


# ---------------------------------------------------------------- command line

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="check the notice against Rule 3 and Sections 5 and 6")
    s = sub.add_parser("show", help="print the notice in one language")
    s.add_argument("--language", default="en")
    p = sub.add_parser("publish", help="write the notice to AWS and make it current")
    p.add_argument("--profile", required=True)
    args = ap.parse_args(argv)

    reg = register.load()
    notice = build(reg)
    ver = version(notice)

    if args.cmd == "show":
        if args.language not in notice["texts"]:
            print(f"Language '{args.language}' is not offered: {', '.join(notice['languages'])}")
            return 1
        print(f"Notice {ver} ({args.language})\n")
        print(notice["texts"][args.language])
        return 0

    problems = check(reg, notice)
    if args.cmd == "check" or problems:
        print(f"Notice {ver}: {len(notice['choices'])} choices, "
              f"{len(notice['not_consent'])} purpose under Section 7, "
              f"languages {', '.join(notice['languages'])}")
        for line in problems:
            print(f"  FAIL {line}")
        print("Result: " + ("PASS" if not problems else f"FAIL ({len(problems)} problems)"))
        if problems or args.cmd == "check":
            return 1 if problems else 0

    import boto3
    ver, changed = publish(boto3.Session(profile_name=args.profile, region_name=REGION), notice)
    print(f"Notice {ver} " + ("published and made current." if changed else
                              "is already the current notice. Nothing changed."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
