# DPDP in Practice: AWS and GitHub Setup Guide

Version of 22 October 2026. Used together with the **Release 1 Build Guide**. This guide builds the platform: the AWS organisation, sign-in, guardrails, logging, evidence storage, cost alerts, and the GitHub settings. The Release 1 guide then builds the model company, **Fernleaf Finance (fictional)**, the personal data register, the tests and the demonstration on top of it.

> **Reading this guide outside the author's build.** It was written for the author's own build and uses his GitHub account name, `riturajb`, and his name in Git settings. Use your own wherever they appear. Where the guide unpacks the starter kit zip (Part 1.4, step 4), download this repository instead (**Code → Download ZIP** on its GitHub page), unpack it in the same place, and use the folder `dpdp-on-aws-main` wherever the guide says `release1-starter-kit`. Part 1.5 describes the author's kit updates; to take a later release, download the repository again.

**What you need before starting**

- A laptop with Windows 10 or 11 (these steps use WSL with Ubuntu), or macOS, or Linux.
- An AWS organisation created through AWS's sign-up flow, with advanced features activated. Activation creates the organisation, its management account (`dpdp-management`) and IAM Identity Center. This guide starts from that state.
- A phone with an authenticator app (Google Authenticator, Microsoft Authenticator or similar).
- The starter kit file `release1_starter_kit.zip`.

**How to read the commands in this guide**

- Each grey box holds exactly one command. Run the boxes in the order of their numbers.
- A command that is too long for one line continues on the next line after a backslash `\`. Copy the whole box and paste it as it is; the terminal treats it as one command.
- Text in angle brackets, such as `<workload id>`, is a value you replace with your own.
- Some steps first set a short value, such as `G=...` or `B=...`, and use it in the next box. The terminal forgets these values when it is closed. If you reopen the terminal partway through a part, run the box that sets the value again before continuing.
- Boxes marked **File content** are not commands. They show what a file must contain.

**Rules for every step**

- Run commands in the Ubuntu terminal unless a step says "console".
- From Part 1.4 onwards, start every working session with this command. All paths in both guides are relative to that folder, and the Python tools need the virtual environment.
  ```bash
  cd ~/work/dpdp-on-aws-workbench && source .venv/bin/activate
  ```
- Every step that Terraform and the tests do not record themselves is recorded in the bootstrap log, `notes/bootstrap-log.md` in the workbench: console clicks, values you are asked to keep, check outputs, and decisions. Part 1.6 explains how. The log stays on the laptop and is never committed or published.
- Never paste account numbers, keys, email addresses or backend files into the public repository.
- After every `terraform plan`, read the plan line by line before applying. If anything is to be destroyed that you did not expect, stop.
- The first `terraform init` in each stack creates a file named `.terraform.lock.hcl`. It records the exact AWS provider version and its checksums, so every later run uses the same version. It holds no secrets and belongs in Git. `git status` lists these files as untracked until they are committed; this is expected. Part 8.3 commits all of them in one pull request.

## Names and values used in both guides

These names are used exactly as written in the setup guide, the Release 1 guide and the code. Replace only the values shown in angle brackets.

| Item | Value |
|---|---|
| Region | Asia Pacific (Mumbai), `ap-south-1`, for every DPDP resource. IAM Identity Center stays in the region where AWS's sign-up flow created it, normally US East (N. Virginia), `us-east-1` |
| Organisational units | `Security`, `Workloads`, `Sandbox` |
| Accounts | `dpdp-management` (the organisation's management account; the console may show it as `<team name> Management Account`), `dpdp-log-archive` and `dpdp-audit` (Security), `dpdp-workload` (Workloads), `dpdp-sandbox` (Sandbox) |
| Accounts created by AWS, not part of the build | Your project account and `Identity Delegated Admin`. Both stay at Root and stay empty |
| Account emails | `<yourname>+dpdp-logarchive@gmail.com`, `+dpdp-audit`, `+dpdp-workload`, `+dpdp-sandbox` |
| Permission sets (IAM Identity Center) | `BreakGlassAdmin` (AdministratorAccess, 1 hour), `PlatformEngineer` (PowerUserAccess and IAMReadOnlyAccess, 4 hours), `Auditor` (ReadOnlyAccess, 4 hours), `ViewOnly` (ViewOnlyAccess, 8 hours) |
| Command-line profiles | `dpdp-mgmt-admin`, `dpdp-logarchive-admin`, `dpdp-logarchive-auditor`, `dpdp-workload-eng`, `dpdp-workload-admin`, `dpdp-sandbox-eng` |
| Terraform state buckets | `dpdp-tfstate-<account id>`, one in each account |
| Guardrail policies | `region` (deny-regions-outside-mumbai), `baseline` (baseline-protections), `buckets` (protect-log-and-evidence-buckets), `cost` (deny-costly-services) |
| Organisation trail | `dpdp-organization-trail`, created in `dpdp-management` |
| Log and evidence buckets (in `dpdp-log-archive`) | `dpdp-cloudtrail-logs-<id>` (governance, 365 days), `dpdp-evidence-live-<id>` (compliance, 30 days), `dpdp-evidence-sandbox-<id>` (governance, 1 day) |
| Model company | Fernleaf Finance (fictional), an Indian lender with a prepaid wallet. Always written with "(fictional)" the first time in each post or document |
| Model company stores | `dpdp-customers`, `dpdp-loans`, `dpdp-wallet-transactions`, `dpdp-support-tickets`, `dpdp-bureau-reports-<id>`, `dpdp-app-events-<id>` |
| Test customer | `C-TEST-0001` (adult borrower), `C-TEST-0002` (teen linked to C-TEST-0001) |
| Local files never committed | `backend.hcl`, `terraform.tfvars`, `config/local.env`, `~/.aws/config`, `data/`, `evidence/`, and the bootstrap log with its saved outputs and screenshots: `notes/bootstrap-log.md`, `notes/outputs/`, `notes/screenshots/` |

---

## Part 1. Prepare the laptop

**Why:** Everything after the console steps is done from the laptop: Terraform creates the AWS resources from code, the AWS command line runs checks, Python runs the tests and tools, and Git records every change. This part installs those tools once.

### 1.1 Install WSL and Ubuntu (Windows only)

**Why:** The tools in this project are built for Linux. WSL runs a real Ubuntu system inside Windows, so the same commands work on Windows, macOS and Linux, and readers of the public repository can repeat every step.

1. Open PowerShell as administrator and run:
   ```powershell
   wsl --install -d Ubuntu-24.04
   ```
2. Restart the laptop.
3. Open **Ubuntu** from the Start menu and create a Linux user name and password.
4. All later commands run in this Ubuntu terminal. Keep the project inside the Linux home folder (`~/work`), not under `/mnt/c`, because file access is much faster there.

### 1.2 Install the tools

**Why:** Each tool has one job. Terraform creates and changes AWS resources from code. The AWS command line talks to AWS from the terminal. tflint and trivy read the Terraform code for mistakes and insecure settings. gitleaks stops passwords and keys from being committed. pre-commit runs these checks automatically before every commit, so a mistake is caught on the laptop rather than in the public repository.

**Basic packages**

1. Install the packages the other tools need:
   ```bash
   sudo apt update && sudo apt install -y unzip curl wget git jq gnupg \
     python3-venv python3-pip software-properties-common pipx
   ```

**AWS CLI version 2**

2. Download the installer:
   ```bash
   curl -sSo /tmp/awscliv2.zip \
     https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip
   ```
3. Unpack and install it:
   ```bash
   unzip -q -o /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install --update
   ```

**Terraform, from HashiCorp's package repository**

4. Add HashiCorp's signing key:
   ```bash
   wget -qO- https://apt.releases.hashicorp.com/gpg \
     | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   ```
5. Add HashiCorp's package source:
   ```bash
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
   https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
     | sudo tee /etc/apt/sources.list.d/hashicorp.list
   ```
6. Install Terraform:
   ```bash
   sudo apt update && sudo apt install -y terraform
   ```

**tflint, from its release file**

7. Go to the temporary folder:
   ```bash
   cd /tmp
   ```
8. Set the download address once, so the next two commands stay short:
   ```bash
   T=https://github.com/terraform-linters/tflint/releases/latest/download
   ```
9. Download tflint and its checksum file:
   ```bash
   curl -sSLO $T/tflint_linux_amd64.zip && curl -sSLO $T/checksums.txt
   ```
10. Verify the download. It must print `tflint_linux_amd64.zip: OK`. If it does not, stop and download again.
    ```bash
    sha256sum --ignore-missing -c checksums.txt
    ```
11. Install tflint:
    ```bash
    unzip -o tflint_linux_amd64.zip && sudo install -c -v tflint /usr/local/bin/
    ```
12. Return to your home folder:
    ```bash
    cd ~
    ```

**trivy, from Aqua Security's package repository**

13. Add trivy's signing key:
    ```bash
    wget -qO- https://aquasecurity.github.io/trivy-repo/deb/public.key \
      | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
    ```
14. Add trivy's package source:
    ```bash
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] \
    https://aquasecurity.github.io/trivy-repo/deb generic main" \
      | sudo tee /etc/apt/sources.list.d/trivy.list
    ```
15. Install trivy:
    ```bash
    sudo apt update && sudo apt install -y trivy
    ```

**pre-commit and gitleaks**

16. Make tools installed with pipx available in the terminal:
    ```bash
    pipx ensurepath
    ```
17. Install pre-commit:
    ```bash
    pipx install pre-commit
    ```
18. Close the Ubuntu terminal and open a new one, so the change from step 16 takes effect.
19. Set the gitleaks download address (version 8.24.2):
    ```bash
    G=https://github.com/gitleaks/gitleaks/releases/download/v8.24.2
    ```
20. Download and install gitleaks:
    ```bash
    curl -sSL $G/gitleaks_8.24.2_linux_x64.tar.gz \
      | sudo tar -xz -C /usr/local/bin gitleaks
    ```

On macOS, install the same tools with one Homebrew command instead of steps 1 to 20:
```bash
brew install awscli terraform tflint trivy gitleaks pre-commit python
```

**Check:** run each of these. Each prints a version number. Terraform must be 1.10 or later.

```bash
aws --version
```
```bash
terraform version
```
```bash
tflint --version
```
```bash
trivy --version
```
```bash
gitleaks version
```
```bash
pre-commit --version
```
```bash
python3 --version
```

Record every version in `notes/tool-versions.md` once the workbench exists (Part 1.4).

### 1.3 Set up Git, commit signing and GitHub access

**Why:** Every change in the public repository carries your name and a cryptographic signature, so a reader can confirm who made it and that it was not altered afterwards. Your email address is kept out of the history to protect your own personal data. The access key lets the laptop send changes to GitHub without a password.

**Keep your email address out of the public history (GitHub website)**

1. In GitHub, open **Settings → Emails**. Tick **Keep my email addresses private** and **Block command line pushes that expose my email**.
2. The same page shows your private address in the form `<id>+riturajb@users.noreply.github.com`. Use it in step 4.

**Your name and address in Git**

3. Set your name:
   ```bash
   git config --global user.name "Rituraj"
   ```
4. Set your private GitHub address:
   ```bash
   git config --global user.email "<id>+riturajb@users.noreply.github.com"
   ```

**Commit signing key**

5. Create the signing key. Press Enter twice when asked for a passphrase, or set one if you prefer.
   ```bash
   ssh-keygen -t ed25519 -C "dpdp signing key" -f ~/.ssh/id_ed25519_signing
   ```
6. Tell Git to sign with SSH keys:
   ```bash
   git config --global gpg.format ssh
   ```
7. Tell Git which key to use:
   ```bash
   git config --global user.signingkey ~/.ssh/id_ed25519_signing.pub
   ```
8. Sign every commit:
   ```bash
   git config --global commit.gpgsign true
   ```
9. Sign every tag:
   ```bash
   git config --global tag.gpgsign true
   ```
10. Print the public signing key, and copy the whole line it prints:
    ```bash
    cat ~/.ssh/id_ed25519_signing.pub
    ```
11. In GitHub: **Settings → SSH and GPG keys → New SSH key**. Set **Key type** to **Signing key**, paste the line, and save. On the same page, tick **Flag unsigned commits as unverified**.

**GitHub access key, used for cloning and pushing**

12. Create the access key. Press Enter twice when asked for a passphrase, or set one.
    ```bash
    ssh-keygen -t ed25519 -C "dpdp github access" -f ~/.ssh/id_ed25519
    ```
13. Print the public access key, and copy the whole line:
    ```bash
    cat ~/.ssh/id_ed25519.pub
    ```
14. In GitHub: **Settings → SSH and GPG keys → New SSH key**. Set **Key type** to **Authentication key**, paste the line, and save.
15. Test the connection. Type `yes` if asked whether to continue connecting. It must print "Hi riturajb! You've successfully authenticated".
    ```bash
    ssh -T git@github.com
    ```

### 1.4 Put the starter kit into the workbench

**Why:** The workbench is your private working copy. The starter kit holds the code, guardrail policies, personal data register and tests for Release 1. Putting it under Git from the first day means every later change is recorded and can be reviewed.

1. Create the work folder and go into it:
   ```bash
   mkdir -p ~/work && cd ~/work
   ```
2. Clone the private workbench:
   ```bash
   git clone git@github.com:riturajb/dpdp-on-aws-workbench.git
   ```
3. Go into it:
   ```bash
   cd dpdp-on-aws-workbench
   ```
4. Unpack the starter kit. Windows files are under `/mnt/c` in Ubuntu; replace `<windows user>` with your Windows user name (for example `Asus`), and adjust the folder if you saved the file elsewhere.
   ```bash
   unzip -o /mnt/c/Users/<windows user>/Downloads/release1_starter_kit.zip \
     -d /tmp/kit
   ```
5. Copy the kit into the workbench:
   ```bash
   cp -r /tmp/kit/release1-starter-kit/. .
   ```
6. Create the Python virtual environment and switch it on:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
7. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```
8. Switch on the checks that run before every commit:
   ```bash
   pre-commit install && pre-commit autoupdate
   ```
9. Format the Terraform files:
   ```bash
   terraform fmt -recursive terraform
   ```
10. Run the register check. It must end with `Result: PASS (0 failures, 6 warnings to review)`.

    **What it checks:** the file `register/personal-data-register.yaml` lists every kind of personal data Fernleaf Finance (fictional) holds. The check confirms that each kind has a purpose, a legal basis, a store, a retention rule and, for each vendor, a contract clause. A **failure** means something required is missing; it stops a commit. A **warning** does not stop anything; it marks a point a person must still confirm. The six warnings are expected at this stage: one vendor (the email provider) is outside India, and five retention periods are placeholders until they are confirmed against the RBI and anti-money-laundering rules.
    ```bash
    python tools/register_check.py
    ```
11. Run the offline tests. They must report `3 passed, 11 skipped`.

    **What the tests are:** Release 1 has 14 tests. Each one tries something the law requires to be true and records the result as evidence. **Offline** tests use only the files in the workbench, so they run anywhere, including on GitHub. **Live** tests try real actions in your AWS accounts, so they are skipped until those accounts exist; the Release 1 guide runs them with `python -m pytest --live`.

    | Test | What it proves | Type |
    |---|---|---|
    | T1 | The register is complete | Offline |
    | T3 | A data flow without a legal basis is blocked | Offline |
    | T4 | One command lists everything held about a customer (on synthetic data) | Offline |
    | T2 | The register matches the stores that exist in the account | Live |
    | T4 (live) | The same customer summary, from the real stores | Live |
    | T5a to T5f | Logs cannot be deleted, shortened or unlocked, and the trail cannot be stopped, even by an administrator (6 tests) | Live |
    | T6 | Storage cannot be created outside Mumbai | Live |
    | T7 | No IAM users with stored passwords or keys, in two accounts (2 tests) | Live |

    The 3 offline tests pass; the 11 live tests are skipped for now. Each test file starts with a short explanation of what it checks, what a pass and a failure mean, and where its evidence is stored.
    ```bash
    python -m pytest
    ```
12. Commit the kit as the first workbench commit. The workbench history is private, so one commit is fine here. The first commit takes a minute longer while pre-commit downloads its tools.
    ```bash
    git add -A && git commit -m "Add Release 1 starter kit"
    ```
13. Push it:
    ```bash
    git push
    ```

### 1.5 Apply a starter kit update

Use this part whenever a new version of the starter kit is issued after Part 1.4 has been done. It copies only the files the new version changed, on a branch, and merges them through a pull request. The file `KIT_CHANGES.md` in the kit lists the changed files for each version.

1. Unpack the new kit. Replace `<windows user>` as in Part 1.4, step 4.
   ```bash
   rm -rf /tmp/kit && \
     unzip -o /mnt/c/Users/<windows user>/Downloads/release1_starter_kit.zip \
     -d /tmp/kit
   ```
   If unzip reports `cannot find or open`, check the name in Downloads. A browser may add a number, such as `release1_starter_kit (1).zip`, or unpack the zip into a folder by itself.
   ```bash
   ls -lt /mnt/c/Users/<windows user>/Downloads/ | grep -i starter
   ```
   For a zip with another name, run step 1 again with that name in double quotes. For a folder (its line starts with `d`), copy it instead of unzipping, replacing `<folder>` with its name:
   ```bash
   rm -rf /tmp/kit && mkdir -p /tmp/kit && \
     cp -r "/mnt/c/Users/<windows user>/Downloads/<folder>/release1-starter-kit" \
     /tmp/kit/
   ```
2. Check that the kit is the version you expect. The first heading printed is the newest version:
   ```bash
   grep -m1 "^## Version" /tmp/kit/release1-starter-kit/KIT_CHANGES.md
   ```
3. Go to the workbench:
   ```bash
   cd ~/work/dpdp-on-aws-workbench && source .venv/bin/activate
   ```
4. Check what is waiting to be committed:
   ```bash
   git status
   ```
   It must say `nothing to commit, working tree clean`, or list only `.terraform.lock.hcl` files as untracked. Those are expected (see "Rules for every step") and are committed with this update in step 11. If any other file is listed, stop and find out why before continuing.
5. Bring main up to date:
   ```bash
   git checkout main && git pull
   ```
6. Create a branch for the update. Every later step of this part runs on this branch.
   ```bash
   git checkout -b kit-update-$(date +%Y%m%d-%H%M)
   ```
7. Read the newest version's entry: the files it changed, and any extra step it needs:
   ```bash
   awk '/^## Version/{n++} n==1' /tmp/kit/release1-starter-kit/KIT_CHANGES.md
   ```
   If you skipped a version, read the whole file and apply every version you have not yet applied, oldest first:
   ```bash
   less /tmp/kit/release1-starter-kit/KIT_CHANGES.md
   ```
   Press **q** to close it.
8. Copy each file listed under the version, one command per file, in this form:
   ```bash
   cp /tmp/kit/release1-starter-kit/<file> <file>
   ```
   If a listed file is new and sits in a folder the workbench does not have yet, the copy fails with `No such file or directory`. Create the folder first, in this form, and copy again:
   ```bash
   mkdir -p <folder>
   ```
   Then carry out any extra step written in the version's entry.
9. Check that only the listed files changed, plus any `.terraform.lock.hcl` files from step 4. If any other file appears, stop.
   ```bash
   git status
   ```
10. Run the offline tests. They must report the same result as in Part 1.4, step 11.
    ```bash
    python -m pytest
    ```
11. Commit. The pre-commit checks run first.
    ```bash
    git add -A && git commit -m "Apply starter kit update of $(date +%d\ %B\ %Y)"
    ```
12. Push the branch:
    ```bash
    git push -u origin HEAD
    ```
13. **Console (GitHub):** open `dpdp-on-aws-workbench` → **Compare & pull request** → **Create pull request**. Wait until all three checks show a green tick. If one fails, select it, open the step with the red cross, and read its log before changing anything. When all three are green: **Merge pull request**, with **Create a merge commit** → **Confirm merge** → **Delete branch**.
14. Return to main and pull the merge:
    ```bash
    git checkout main && git pull
    ```
15. Delete the update branch on the laptop as well. **Delete branch** on GitHub removes only GitHub's copy; the laptop keeps its own until it is deleted here. `-d` refuses to delete a branch whose work is not in main.
    ```bash
    git branch -d $(git branch --list "kit-update-*" --format="%(refname:short)")
    ```
16. Check that only main is left:
    ```bash
    git branch
    ```

### 1.6 The bootstrap log: a record of what you do by hand

**Why:** Three parts of this build keep their own records. Git records the code. Terraform records what it has built, in its state. The tests write an evidence record of every result to a locked bucket. Nothing records the steps done by hand: the root user's MFA, IAM Identity Center, the permission sets and who holds them, the removal of root credentials, the checks read on screen, and the decisions taken along the way. The bootstrap log is that record.

It answers, with a date and saved output, the questions an auditor asks about any platform: who holds administrator access and since when, when root credentials were removed, and how each guardrail was tested before anything relied on it. It also keeps every value you need again, such as account ids and bucket names, in the saved outputs.

**How it works.** You never type into the log. Every entry is made by one command, `scripts/log_step.sh`, which adds a dated line to the log. Where the step has a command whose output proves it, the script also runs that command and saves its output. This guide shows each of these commands at the step where it belongs.

| Item | What it holds |
|---|---|
| `notes/bootstrap-log.md` | The activity log: one line per entry, with the date and time in IST, the part of this guide, what was done or decided, and the name of the saved output |
| `notes/outputs/` | One text file per saved command output, with the part, time, note and command at the top |
| `notes/screenshots/` | Console pages that are the only proof of a step |
| `notes/bootstrap-log.template.md` | The empty log, part of the kit. The script copies it once, on first use |

**Private, and never shown.** The log, the outputs and the screenshots contain account ids, the organisation id and email addresses. Git ignores all three, so they never reach the workbench or the public repository. None of them appears in the demonstration video: the video is drawn from the results of `scripts/demo_release1.sh`, shows only the lines that prove each point, and masks every id (Release 1 guide, Step 7). If a public post ever needs a picture of a console page, take a new screenshot for that purpose and blank the account numbers; never reuse one from `notes/screenshots/`.

The other files in `notes/` are different. `notes/tool-versions.md`, `notes/decisions.md` and `notes/releases.md` hold no ids and are committed to the workbench as usual.

**Set it up (once)**

1. Check that Git ignores the private files. The command must print three lines, each naming `.gitignore`. If it prints nothing, the kit update of 22 October 2026 has not been applied yet (Part 1.5).
   ```bash
   git check-ignore -v notes/bootstrap-log.md notes/outputs/x notes/screenshots/x
   ```
2. Check that no earlier copy of the log is in Git. The list must not include `notes/bootstrap-log.md`.
   ```bash
   git ls-files notes
   ```
   If it does, the file was committed before Git was told to ignore it. Take it out of Git while keeping it on the laptop, then commit and merge the change through a branch and pull request, as in Part 1.5, steps 6 and 11 to 16:
   ```bash
   git rm --cached notes/bootstrap-log.md
   ```
3. Start the log. The first use copies the template to `notes/bootstrap-log.md`, creates the folders `notes/outputs` and `notes/screenshots`, and adds the first line.
   ```bash
   scripts/log_step.sh 1.6 "Bootstrap log started"
   ```
4. Find the `notes` folder from Windows, for saving screenshots. Print your Ubuntu user name:
   ```bash
   whoami
   ```
   In Windows File Explorer, type `\\wsl.localhost` in the address bar and press Enter. Open the Ubuntu folder shown there (its name may be `Ubuntu` or `Ubuntu-24.04`), then `home` → your Ubuntu user name → `work` → `dpdp-on-aws-workbench` → `notes`. Right-click `notes` in the left pane → **Pin to Quick access**.

**The three kinds of entry**

**A. A step done in the console, or a decision.** One line, in this form:
```bash
scripts/log_step.sh 3.3 \
  "Identity Center: primary region us-east-1, identity source AWS Builder ID"
```
A decision starts with `Decision:`, and says what was decided and why. For example:
```bash
scripts/log_step.sh 3.3 \
  "Decision: Identity Center stays in us-east-1; AWS cannot move it"
```

**B. A command whose output proves a step.** Put `scripts/log_step.sh <part> "<what this shows>" --` in front of the command. For example, the trail check in Part 7.3:
```bash
scripts/log_step.sh 7.3 "Organisation trail is logging" -- \
  aws cloudtrail get-trail-status --name dpdp-organization-trail \
  --profile dpdp-mgmt-admin --query IsLogging
```
The command runs as usual and its output appears on screen. In addition, the script saves a copy in `notes/outputs/<date>-<time>-part-7.3.txt` and adds a line to the log naming that file. If the command fails, its exit code is added to both. A failed command is still logged on purpose: in the guardrail tests of Part 9, the refusal is the expected result, so the saved failure is the evidence that the guardrail works.

Inside a Terraform stack folder, call the script as `../../../../scripts/log_step.sh`.

**C. A screenshot**, for the few steps where only a console page shows the result. This guide names each one at its step: `3.2-policies-on-root.png`, `3.4-permission-sets.png`, `5.1-permission-sets-provisioned.png`, `5.3-root-credentials-not-present.png` and `8-budget-alerts.png`.

To save one:

1. Press **Windows + Shift + S** and drag around the part of the page to keep.
2. Click the notification that appears at the bottom right. Snipping Tool opens with the picture.
3. Press **Ctrl + S**. In the **Save As** window, open the pinned `notes` folder, then `screenshots`.
4. Type the file name given in the step and choose **Save**.
5. Log it, in this form:
   ```bash
   scripts/log_step.sh 5.3 \
     "Screenshot 5.3-root-credentials-not-present.png: all four Not present"
   ```

If Snipping Tool has already saved the picture by itself in `Pictures\Screenshots`, copy it from there instead of steps 3 and 4, with the file name it was given:
```bash
cp "/mnt/c/Users/<windows user>/Pictures/Screenshots/<file name>.png" \
  notes/screenshots/5.3-root-credentials-not-present.png
```

**Back it up.** The log is not in Git, so a lost or broken laptop would lose it. Create a backup folder in a Windows folder that is backed up, such as your OneDrive (check its name in File Explorer; it may be `OneDrive - Personal`):
```bash
mkdir -p "/mnt/c/Users/<windows user>/OneDrive/dpdp-bootstrap-notes"
```
At the end of each working session, copy the notes into it:
```bash
cp -r -u notes/. "/mnt/c/Users/<windows user>/OneDrive/dpdp-bootstrap-notes/"
```

**If you reach this part after Part 2 or later.** Run the logging commands of the parts you have already done, as they appear at their steps in this guide. The commands that read from AWS are safe to run again; they only read. Where you do not remember the day a step was done, the log shows the day you checked it, which is what it records.

**Check:** `notes/bootstrap-log.md` exists, it has at least one line under "Activity log", and `git status` does not list it.

---

## Part 2. Secure the management account

**Why:** The management account owns the organisation and pays for every account in it. Whoever controls it controls everything. These steps close the most common ways in: a root user without MFA, root access keys, and security notices that reach nobody.

All steps in the AWS console, signed in as the **root user of the management account**: the email address and password set when advanced features were activated. In AWS Organizations, this account carries the label **management account**. In both guides it is called `dpdp-management`.

AWS verifies a new account before every service is available, which can take up to two days. If any step fails with "account verification is in progress", wait and try that step again later.

1. **Region:** top right of the console, choose **Asia Pacific (Mumbai)**. Then make it the default: gear icon → **See all user settings** → **Localization and default Region** → **Edit** → **Default Region:** Asia Pacific (Mumbai) → **Save settings**.
2. **Multi-factor authentication for the root user:** account menu (top right) → **Security credentials** → **Multi-factor authentication** → **Assign MFA device** → **Authenticator app**. Scan the code and enter two codes.
3. **Root access keys:** on the same page, under **Access keys**, delete any key that exists. There must be none.
4. **Alternate contacts:** account menu → **Account** → **Alternate contacts**. Add yourself for Billing, Operations and Security.
5. **IAM access to billing:** account menu → **Account** → **IAM user and role access to Billing information** → **Edit** → tick **Activate IAM Access** → **Update**. Without this, Identity Center users cannot see costs.
6. **Plan:** open **Billing and Cost Management**. The account is on the **Paid plan**, because it manages an organisation. Free Tier credits do not apply inside an organisation; AWS does not reinstate them. The build is paid from the start and capped by the budget in Part 8.
7. **Password:** store the root password in a password manager. The root user is still needed for Parts 3.1 to 3.4, because no other sign-in has access yet. From Part 3.4, step D, onwards, root is used only for the few tasks that require it.

**Check:** the IAM dashboard shows "Root user has MFA" and no root access keys.

8. Log it. The command line does not work yet, so this is a line of text; Part 3.5, step 9, adds the proof from AWS once it does.
   ```bash
   scripts/log_step.sh 2 \
     "Console: Mumbai region, root MFA, no keys, contacts, billing access, Paid plan"
   ```

---

## Part 3. Check the organisation and set up sign-in

**Why:** Terraform in Part 4 must work with the organisation as it actually is, and you need a way to sign in that is not the root user.

AWS's sign-up flow has already created the organisation and IAM Identity Center. This part records what exists, checks the guardrails AWS attached, and sets up your sign-in. Nothing here is created twice.

### 3.1 Record the organisation (console)

**Why:** Terraform needs the organisation id in Part 4. The account list shows which accounts belong to the build and which were created by AWS and stay out of it.

1. Open **AWS Organizations** → **AWS accounts**. Find the **organisation id** (`o-` followed by ten characters, bottom left). It goes into `terraform.tfvars` in Part 4. Part 3.5, step 9, saves it in the bootstrap log from the command line.
2. Three accounts sit at **Root**, with no organisational units yet:

| Account | What it is | Use in this build |
|---|---|---|
| `<team name>` Management Account | The management account (`dpdp-management`). It owns the organisation and pays all bills. Guardrails never apply to it | All management steps |
| Your project account | Created by the sign-up flow. Owned through your AWS Builder ID. AWS does not allow it to be removed from the organisation | None. Keep it empty |
| Identity Delegated Admin | Created by AWS. Holds the administrator rights for IAM Identity Center | None. Leave it as it is |

3. Find the three account ids in the list. Part 3.5, step 9, saves them in the bootstrap log.
4. **Policies:** note that **Service control policies** and **Resource control policies** both show **Enabled**.
5. **Services:** note the services that show trusted access as enabled. The Terraform in Part 4 keeps every one of them and adds the ones this build needs.
6. Log the decision:
   ```bash
   scripts/log_step.sh 3.1 \
     "Decision: organisation from AWS sign-up flow; Terraform imports it in Part 4"
   ```

### 3.2 Check the guardrails AWS attached (console)

AWS attaches its own guardrails to organisations created through its sign-up flow. One of them restricts regions. If that one sits on Root, it would apply to every DPDP account and block Mumbai, so it is checked now.

1. **AWS Organizations** → **AWS accounts** → select **Root** → **Policies** tab.
2. Under **Service control policies**, open each policy attached to Root, one at a time, and read its JSON.
3. Apply this rule:

| What the policy contains | What to do |
|---|---|
| `FullAWSAccess` | Keep. AWS attaches it by default |
| `BlockOrgEscape` and `ProtectManagedRoles` | Keep. It stops accounts leaving or being closed from inside, and protects AWS's own roles under `role/managed/`. It cannot be changed and does not affect this build |
| `RegionFloor` (allows only `us-east-1`, `us-west-2` and one selected region) | **Do not continue.** On the policy's **Targets** tab, detach it from Root and attach it to your project account instead. If AWS refuses the change, stop and open a support case: the DPDP accounts cannot use Mumbai while it sits on Root |

4. Under **Resource control policies**, open each policy attached to Root:

| What the policy contains | What to do |
|---|---|
| `RCPFullAWSAccess` | Keep. AWS attaches it by default |
| `DenyAnyoneOutsideMyOrgAndAWS` | Keep. Only principals inside the organisation, and AWS services acting for it, can reach S3, KMS, DynamoDB and similar resources. It matches this build's design |

5. Select each of the three accounts in turn and repeat steps 2 to 4 on its **Policies** tab, so you know what applies to each account directly.
6. Save the screenshot `3.2-policies-on-root.png` of the Root **Policies** tab (Part 1.6), and log it, with what you found about `RegionFloor`:
   ```bash
   scripts/log_step.sh 3.2 \
     "Screenshot 3.2-policies-on-root.png; no RegionFloor policy on Root"
   ```

**Check:** no policy containing `RegionFloor` is attached to Root.

### 3.3 Record IAM Identity Center and set up MFA (console)

**What IAM Identity Center is.** IAM works inside one account: its users, roles and policies apply to that account only. IAM Identity Center is one sign-in for all accounts in the organisation. You sign in once, with MFA, choose an account, and receive **temporary** access as a role in that account. A **permission set** is a template for that role: when a permission set is assigned to an account, Identity Center creates an ordinary IAM role there, named `AWSReservedSSO_<permission set>_...`. It is still IAM underneath; Identity Center creates and manages the roles in every account.

**Why this build uses it rather than IAM users:**

| | IAM users only | IAM Identity Center |
|---|---|---|
| Accounts to manage | One user per person in each of the five accounts | One user, with access to all five |
| Command line | Long-lived access keys stored on the laptop | Temporary credentials from `aws sso login`; no keys stored |
| MFA | Set up per user, per account | Once |
| Logs | Separate users in separate accounts | One named person in a named role, everywhere |
| Removing someone | Delete them from every account | Remove once; access ends everywhere |
| Cost | Free | Free |

Rule 6(1)(b) requires access control, and test T7 proves that no account holds IAM users with stored passwords or keys.

**Root user and your Identity Center user are two different sign-ins,** even though they use the same email address:

| | Root user of the management account | Your Identity Center user (Builder ID) |
|---|---|---|
| Sign-in | Console, "Root user", email and password | The access portal URL, or `aws sso login` |
| What it can do | Everything, always; nothing can restrict it | Nothing, until a permission set is assigned to it |
| Session | Until you sign out | Ends after the permission set's session duration |
| Command line | Only with root access keys, which this build forbids | Yes, through `aws sso login` |
| In the logs | "root" | `AWSReservedSSO_BreakGlassAdmin/<your user>` |

Root is the last resort. BreakGlassAdmin is the strongest everyday access, used for setup tasks. Each sign-in has its own password and its own MFA: the root MFA from Part 2 does not protect the Identity Center user.

The AWS console steps in 3.3 and 3.4 are done signed in as the root user, because no Identity Center access exists yet. Step 3 of 3.3 is the exception: the Builder ID profile uses your Builder ID sign-in.

1. Open **IAM Identity Center** → **Settings**. If the console shows no instance, switch the region to **US East (N. Virginia)**: the sign-up flow creates Identity Center there.
2. Read these three settings. Step 4 logs them.
   - **Primary Region** (normally `us-east-1`). AWS cannot move an instance to another region. Sign-in data stays in that region; every DPDP resource stays in Mumbai.
   - **AWS access portal URL, Dual-stack** (`https://ssoins-…portal.<region>.app.aws`), under **Identity source** → **AWS access portal URLs**. It goes into the command-line configuration in Part 3.5. Do not use the IPv4-only link there: the command line does not accept it as a start URL for this kind of instance.
   - **Identity source:** AWS Builder ID. Your Identity Center user is your Builder ID. Keep this source: AWS does not allow a change away from Builder ID to be reversed.
3. **MFA for your Identity Center user:** open your Builder ID profile at `https://profile.aws.amazon.com` → **Security** → register an authenticator app. It can sit in the same authenticator app as the root MFA, as a separate entry. Sign out and sign in again to confirm it asks for the code.
4. Log the settings and the MFA:
   ```bash
   scripts/log_step.sh 3.3 \
     "Identity Center: region us-east-1, source AWS Builder ID, Builder ID MFA on"
   ```
5. Log the decision that comes with the region:
   ```bash
   scripts/log_step.sh 3.3 \
     "Decision: Identity Center stays in us-east-1; AWS cannot move it"
   ```

### 3.4 Create the permission sets and assign your access (console)

**Why:** A permission set decides what a person may do in an account. Assigning `BreakGlassAdmin` to the management account gives your Identity Center user the access needed for Parts 3.5 to 10, so the root user can be put away.

All in **IAM Identity Center**, region **US East (N. Virginia)**, signed in as the root user of the management account.

**Switch on multi-account permissions.** The sign-up flow leaves this off; until it is on, the left menu has no **Multi-account permissions** section.

1. **Settings** → **Management** tab.
2. In **Enable multi-account permissions**, choose **Enable**, and confirm if asked.
3. Wait until **Status** shows **Enabled**, then refresh the page. The left menu now shows **Multi-account permissions**, with **AWS accounts** and **Permission sets**.

**A. Three predefined permission sets.** Each permission set holds exactly one policy, so the wizard runs three times, once per row:

| Round | Policy to select | Permission set name | Session duration |
|---|---|---|---|
| 1 | AdministratorAccess | `BreakGlassAdmin` | 1 hour |
| 2 | ReadOnlyAccess | `Auditor` | 4 hours |
| 3 | ViewOnlyAccess | `ViewOnly` | 8 hours |

**`Auditor` and `ViewOnly` are different.** `Auditor` (ReadOnlyAccess) can read configurations **and contents**: S3 objects, DynamoDB items and log files. It is for someone who must examine logs and evidence. `ViewOnly` (ViewOnlyAccess) can see which resources exist and how they are configured, but **cannot read their contents**. It is for someone who checks, for example, that the stores are encrypted and tagged, and has no reason to see customers' personal data. Giving each person only the access their work needs is what Rule 6(1)(b) asks for.

For each round:

1. **Multi-account permissions** → **Permission sets** → **Create permission set**.
2. **Permission set type:** **Predefined permission set**.
3. **Policy for predefined permission set:** select the round's policy (one radio button). Choose **Next**.
4. **Permission set name** and **Session duration** from the round's row. Leave description and relay state empty. Choose **Next**.
5. Check the summary and choose **Create**.

**B. The custom permission set `PlatformEngineer`:**

1. **Permission sets** → **Create permission set** → **Custom permission set** → **Next**.
2. Expand **AWS managed policies**. Search for and tick **PowerUserAccess**, then search for and tick **IAMReadOnlyAccess**. Leave the other sections empty. Choose **Next**.
3. **Permission set name:** `PlatformEngineer`. **Session duration:** 4 hours. Choose **Next**, then **Create**.

**Check:** the **Permission sets** page lists four entries. Save the screenshot `3.4-permission-sets.png` (Part 1.6), and log it:
```bash
scripts/log_step.sh 3.4 "Screenshot 3.4-permission-sets.png: four permission sets"
```

**C. Give your Identity Center user access to the management account:**

1. **Multi-account permissions** → **AWS accounts**.
2. Tick the management account (`<team name> Management Account`).
3. **Assign users or groups** → **Users** tab → tick your user (your Builder ID) → **Next**.
4. Tick **BreakGlassAdmin** → **Next** → **Submit**. Wait until the page shows that provisioning succeeded.

**D. Stop using root:**

1. Sign out of the root user.
2. Open the access portal URL from Part 3.3 and sign in with your Builder ID and its MFA.
3. The portal lists the management account with **BreakGlassAdmin**. From here on, use this sign-in for console work. Root is used only for the few tasks that require it.

### 3.5 Command-line sign-in

**Why:** Everything run from the laptop needs AWS credentials: Terraform, the AWS command line, the scripts, and the Python tests and tools, which reach AWS through the boto3 library. `aws sso login` obtains **temporary** credentials for your Identity Center user and keeps them on the laptop until the session ends. Every tool then finds them through a profile name in `~/.aws/config`, such as `dpdp-mgmt-admin`, which says which account and which permission set to use. No access keys are ever stored, which is what Rule 6(1)(b) and test T7 require.

1. Go to the workbench (if you are not there already):
   ```bash
   cd ~/work/dpdp-on-aws-workbench && source .venv/bin/activate
   ```
2. Create the AWS configuration folder:
   ```bash
   mkdir -p ~/.aws
   ```
3. Copy the profile template into your AWS configuration:
   ```bash
   cat config/aws-config.example >> ~/.aws/config
   ```
4. Open the configuration in an editor:
   ```bash
   nano ~/.aws/config
   ```
5. The file now holds the template from step 3. Change **two lines**; leave everything else as it is. Move with the arrow keys.

   **Change these two:**

   - Near the top, under `[sso-session dpdp]`, the start URL line. Replace the whole address with your Dual-stack access portal URL (IAM Identity Center → **Settings** → **Identity source** tab → **AWS access portal URLs** → the **Dual-stack** link, ending in `.app.aws`):
     ```
     sso_start_url = <Dual-stack access portal URL>
     ```
   - Under `[profile dpdp-mgmt-admin]` **only**, replace `111111111111` with the management account id (AWS Organizations → **AWS accounts** → the 12-digit number under the account marked **management account**):
     ```
     sso_account_id = <management account id>
     ```

   **Check, normally already correct:** `sso_region` under `[sso-session dpdp]` must match **Primary Region** in IAM Identity Center → **Settings** → **Details**. For an organisation created through AWS's sign-up flow it is `us-east-1`, which the template already holds.

   **Leave these profiles exactly as they are:**

   - `[profile dpdp-logarchive-admin]` and `[profile dpdp-logarchive-auditor]` (`222222222222`)
   - `[profile dpdp-workload-eng]` and `[profile dpdp-workload-admin]` (`333333333333`)
   - `[profile dpdp-sandbox-eng]`, further down

   Their numbers are placeholders for the log archive, workload and sandbox accounts, which do not exist yet. Terraform creates them in Part 4, and their real ids go in at Part 5.2. Do not change any `region = ap-south-1` line.

   Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
6. Sign in:
   ```bash
   aws sso login --sso-session dpdp
   ```
   Ubuntu in WSL cannot open the Windows browser itself, so the command prints a long link starting `https://oidc.` and waits. Copy that link into your browser on Windows, sign in with your Builder ID and its MFA, and choose **Allow access**. The browser hands control back to the terminal, which prints `Successfully logged into Start URL`. Every later sign-in in both guides works the same way.

   To have the browser open by itself in future, install the WSL helper once:
   ```bash
   sudo apt install -y wslu
   ```
   Then make it the terminal's browser:
   ```bash
   echo 'export BROWSER=wslview' >> ~/.bashrc && source ~/.bashrc
   ```
7. Check who you are signed in as, and keep the output in the bootstrap log (Part 1.6):
   ```bash
   scripts/log_step.sh 3.5 "Sign-in check, management account" -- \
     aws sts get-caller-identity --profile dpdp-mgmt-admin
   ```

**Check:** the output shows the management account id and an `Arn` containing `AWSReservedSSO_BreakGlassAdmin`. When a later command reports an expired token, run step 6 again.

8. Record what is already enabled in the organisation. The plan in Part 4 is compared with this output.
   ```bash
   scripts/log_step.sh 3.5 "Trusted services before Part 4" -- \
     aws organizations list-aws-service-access-for-organization \
     --query "EnabledServicePrincipals[].ServicePrincipal" \
     --output table --profile dpdp-mgmt-admin
   ```
9. Save the organisation id and the management account id, recorded by hand in Part 3.1:
   ```bash
   scripts/log_step.sh 3.1 "Organisation id and management account id" -- \
     aws organizations describe-organization --profile dpdp-mgmt-admin \
     --query "Organization.[Id,MasterAccountId]" --output text
   ```
10. Save the root user's MFA and access keys, checked by hand in Part 2. It must print `1` and `0`: MFA on, no access keys.
    ```bash
    scripts/log_step.sh 2.2 "Root MFA on (1) and no root access keys (0)" -- \
      aws iam get-account-summary --profile dpdp-mgmt-admin \
      --query "SummaryMap.[AccountMFAEnabled,AccountAccessKeysPresent]" --output text
    ```
11. Save the alternate contacts from Part 2. It must print three lines, Billing, Operations and Security, each with a name.
    ```bash
    scripts/log_step.sh 2.4 "Alternate contacts set" -- bash -c \
      'for t in BILLING OPERATIONS SECURITY; do aws account get-alternate-contact \
      --alternate-contact-type $t --profile dpdp-mgmt-admin \
      --query "AlternateContact.[AlternateContactType,Name]" --output text; done'
    ```

---

## Part 4. Create the member accounts with Terraform

**Why:** The DPDP accounts are created from code rather than by hand. Their settings are written down, every change is shown in a plan before it happens, and the code itself can be shown to an auditor. Separate accounts keep the logs and evidence apart from the systems that hold personal data, so a mistake or a compromise in one does not reach the other.


**What the organisation will look like after this part.** Terraform creates three organisational units (OUs) and four DPDP accounts. The three accounts that already exist stay at Root.

| Where | Account | What it holds | Guardrails attached in Part 9 |
|---|---|---|---|
| Root | Management account (`dpdp-management`) | The organisation, billing, IAM Identity Center administration, the organisation trail and the budget. No personal data and no workloads | None: AWS never applies guardrails to the management account |
| Root | Your project account | Created by AWS's sign-up flow. Not part of the build; stays empty | None from this build |
| Root | Identity Delegated Admin | Created by AWS to administer IAM Identity Center. Not part of the build | None from this build |
| Security OU | `dpdp-log-archive` | The audit logs of every account, and the test evidence, locked under Object Lock | region, baseline, buckets |
| Security OU | `dpdp-audit` | Reserved for security monitoring and the auditor's read-only work in later releases. Empty in Release 1 | region, baseline, buckets |
| Workloads OU | `dpdp-workload` | **Production** for Fernleaf Finance (fictional): its six data stores, with synthetic data | region, baseline, buckets, cost |
| Sandbox OU | `dpdp-sandbox` | **Test**: trials, the first guardrail tests, and the clean-room test of each release | region, baseline, cost |

**Why three OUs.** An OU groups accounts that need the same guardrails, so a rule is attached once to the OU rather than to each account. **Security** keeps the records about the system (logs and evidence) away from the system that holds personal data, so nobody working on that data can reach or change them; Rule 6(1)(c) and Rule 6(1)(e) depend on this separation. **Workloads** holds the personal data and receives every guardrail. **Sandbox** is where mistakes are allowed: each guardrail is tried there first.

**Production and test.** `dpdp-workload` is the production account of Fernleaf Finance (fictional): the demonstration and the live tests run against it. `dpdp-sandbox` is the test account. A real company would usually split workloads further, for example separate development and production accounts inside the Workloads OU; this build uses one workload account to keep costs low, and a further account can be added to the same OU later without changing anything else.

**Code and accounts are different things.** The workbench (private) and the public repository `dpdp-on-aws` hold the code. The AWS accounts are real environments that the code creates and changes. Nothing in AWS is stored in the repositories, and no account details are stored in Git.

### 4.1 State bucket for the management account

**Why:** Terraform keeps a record, called state, of everything it has created. It is kept in an encrypted, versioned bucket in the same account rather than on the laptop, so it is not lost, and a lock stops two runs from changing the same resources at once.

1. Create the bucket that stores Terraform's state for this account:
   ```bash
   scripts/bootstrap_state_bucket.sh dpdp-mgmt-admin
   ```
2. It prints two lines (`bucket = ...` and `profile = ...`). Keep them for Part 4.2.

### 4.2 Organisation stack

**Why:** This stack takes over the existing organisation and creates the three organisational units, the four DPDP accounts and the four guardrail policies. The guardrails are created here but attached only in Part 9.

1. Go to the organisation stack:
   ```bash
   cd terraform/live/management/organization
   ```
2. Create the backend file from its template:
   ```bash
   cp backend.hcl.example backend.hcl
   ```
3. Open it and paste the two lines printed in Part 4.1. Save and close.
   ```bash
   nano backend.hcl
   ```
4. Create the variables file from its template:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
5. Open it:
   ```bash
   nano terraform.tfvars
   ```
   Change two things; leave the `scp_attachments` block as it is (it stays empty until Part 9).

   **File content** (before):

   ```
   organization_id = "o-xxxxxxxxxx"

   account_emails = {
     "log-archive" = "yourname+dpdp-logarchive@gmail.com"
     "audit"       = "yourname+dpdp-audit@gmail.com"
     "workload"    = "yourname+dpdp-workload@gmail.com"
     "sandbox"     = "yourname+dpdp-sandbox@gmail.com"
   }
   ```

   - `organization_id`: replace `o-xxxxxxxxxx` with the organisation id recorded in Part 3.1, keeping the quotation marks.
   - The four email addresses: replace `yourname` with the part of your Gmail address before the `@`. For example, with `asha.rao@gmail.com` the first line becomes `"log-archive" = "asha.rao+dpdp-logarchive@gmail.com"`.

   **Why four different addresses:** AWS requires every account to have its own root email address, used by no other AWS account. Gmail delivers any address of the form `name+anything@gmail.com` to the inbox of `name@gmail.com`, so all four reach your one inbox while AWS sees four different addresses. The text after the `+` shows which account a message is about.

   Save with **Ctrl+O**, Enter, and close with **Ctrl+X**. Git ignores this file, so the addresses and the organisation id never reach the repository.
6. Initialise Terraform:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
7. Prepare the plan:
   ```bash
   terraform plan -out=org.tfplan
   ```

**Read the plan.** It must show:

- 1 resource to import (the organisation) and **no** resource to destroy
- 3 organisational units, 4 accounts, 4 policies to add
- 0 policy attachments (guardrails are attached later, in stages)
- The organisation itself shows 1 change: `cloudtrail.amazonaws.com` is **added** to `aws_service_access_principals`. Every service recorded in Part 3.5, step 8, stays in the list, and `enabled_policy_types` keeps both `RESOURCE_CONTROL_POLICY` and `SERVICE_CONTROL_POLICY`. If the plan **removes** anything from either list, stop
- The project account and Identity Delegated Admin do not appear in the plan. Terraform does not manage them

8. Apply the plan:
   ```bash
   terraform apply org.tfplan
   ```
   A new organisation can start with an account limit below AWS's usual 10. If the apply stops with `You have exceeded the allowed number of AWS accounts`, see Troubleshooting: the organisational units and policies are already created, and only the accounts wait for a higher limit.
9. Show the new account ids and save them in the bootstrap log:
   ```bash
   ../../../../scripts/log_step.sh 4.2 "New account ids" -- \
     terraform output account_ids
   ```
   If AWS had to raise the account limit first (see Troubleshooting), log that too, with your support case number:
   ```bash
   ../../../../scripts/log_step.sh 4.2 \
     "Decision: account limit raised by AWS, support case <case number>"
   ```
10. Return to the workbench folder:
    ```bash
    cd ~/work/dpdp-on-aws-workbench
    ```

Account creation takes a few minutes per account.

**Check:** AWS Organizations in the console shows the Security, Workloads and Sandbox units and the four accounts inside them. The management account, the project account and Identity Delegated Admin stay at Root.

---

## Part 5. Access to the new accounts

**Why:** The four new accounts exist, but nobody can sign in to them yet. This part gives your Identity Center user the access each account needs, and nothing more.

### 5.1 Assign permission sets (console, IAM Identity Center → AWS accounts)

**Why:** Each account gets only the permission sets its work needs. For example, the log archive account gets `Auditor` for reading logs, and no engineering access, because nobody should change logs there. The audit account gets `Auditor` for everyday review work. `BreakGlassAdmin` is assigned to every account as the one administrator route, used only for setting the account up and in emergencies; its sessions last one hour and every use is recorded by the organisation trail.

| Account | Permission sets for your user |
|---|---|
| `dpdp-management` | BreakGlassAdmin (already done) |
| `dpdp-log-archive` | BreakGlassAdmin, Auditor |
| `dpdp-audit` | Auditor, BreakGlassAdmin |
| `dpdp-workload` | BreakGlassAdmin, PlatformEngineer, Auditor, ViewOnly |
| `dpdp-sandbox` | BreakGlassAdmin, PlatformEngineer |

For each of the four new accounts, signed in through the access portal with `BreakGlassAdmin` on the management account, or as root if that is not yet possible:

1. **IAM Identity Center** (region **US East (N. Virginia)**) → **Multi-account permissions** → **AWS accounts**.
2. Tick the account.
3. **Assign users or groups** → **Users** tab → tick your user (your Builder ID) → **Next**.
4. Tick every permission set listed for that account in the table above → **Next** → **Submit**.
5. Wait until the page shows that provisioning succeeded.

**Check:** **Multi-account permissions** → **Permission sets** shows all four permission sets as **Provisioned**. Save the screenshot `5.1-permission-sets-provisioned.png` (Part 1.6), and log it:
```bash
scripts/log_step.sh 5.1 \
  "Screenshot 5.1-permission-sets-provisioned.png: assigned as in the table"
```

### 5.2 Profiles

**Why:** A profile ties a name to one account and one permission set. Every command then names the profile it uses, so it is always clear which account a command acts on.

1. Open the AWS configuration:
   ```bash
   nano ~/.aws/config
   ```
2. Replace the placeholder `sso_account_id` in each remaining profile with the real account id printed by `terraform output account_ids` in Part 4.2, step 9. Each placeholder stands for one account, so profiles for the same account get the same id:

   | Placeholder in the file | Replace with the id of | Profiles that use it |
   |---|---|---|
   | `222222222222` | `dpdp-log-archive` | `dpdp-logarchive-admin`, `dpdp-logarchive-auditor` |
   | `333333333333` | `dpdp-workload` | `dpdp-workload-eng`, `dpdp-workload-admin` |
   | `444444444444` | `dpdp-sandbox` | `dpdp-sandbox-eng` |

   The audit account has no command-line profile in Release 1, because no command runs there. Its profiles are added in the release that builds it.

   Leave `dpdp-mgmt-admin` as it is (set in Part 3.5) and do not change any `sso_role_name` or `region` line. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
3. Sign in again:
   ```bash
   aws sso login --sso-session dpdp
   ```
4. Check all five profiles in one go, and keep the output in the bootstrap log. This is one command over four lines; paste it as it is.
   ```bash
   scripts/log_step.sh 5.2 "Five profile checks" -- bash -c \
     'for p in dpdp-logarchive-admin dpdp-logarchive-auditor dpdp-workload-eng \
     dpdp-workload-admin dpdp-sandbox-eng; do echo "$p: $(aws sts get-caller-identity \
     --profile $p --query Arn --output text)"; done'
   ```

**Check:** five lines, each showing the right account and permission set.

### 5.3 Remove root credentials from the member accounts (console)

**Why:** Each new account starts with a root user that nobody needs. Removing its credentials means nobody can sign in as root there; the few root tasks are run centrally from the management account.

This must be done before guardrail stage A, because the `baseline` guardrail blocks the root user.

1. **IAM** (management account) → **Root access management** → **Enable**. Tick **Root credentials management** and **Privileged root actions in member accounts**.
2. For each of the four member accounts: select it → **Take privileged action** → **Delete root user credentials** (if the option shows credentials present).
3. Save the screenshot `5.3-root-credentials-not-present.png` (Part 1.6), and log it:
   ```bash
   scripts/log_step.sh 5.3 "Root credentials of the four member accounts: Not present"
   ```

---

## Part 6. State buckets and baselines in the member accounts

**Why:** Each account keeps its own Terraform state. The baseline then switches on three account-wide protections before anything else is built: no S3 bucket can be made public, every new disk is encrypted, and IAM Access Analyzer reports anything reachable from outside the account. These support Rule 6(1)(a) and Rule 6(1)(b).

**State buckets**

1. Create the state bucket in the log archive account:
   ```bash
   scripts/log_step.sh 6.1 "State bucket, log archive account" -- \
     scripts/bootstrap_state_bucket.sh dpdp-logarchive-admin
   ```
2. Create the state bucket in the workload account:
   ```bash
   scripts/log_step.sh 6.2 "State bucket, workload account" -- \
     scripts/bootstrap_state_bucket.sh dpdp-workload-eng
   ```
3. Create the state bucket in the sandbox account:
   ```bash
   scripts/log_step.sh 6.3 "State bucket, sandbox account" -- \
     scripts/bootstrap_state_bucket.sh dpdp-sandbox-eng
   ```

Each command prints two lines, a `bucket` line and a `profile` line, for its own account. Keep all three pairs; each pair is used once below. They are also saved in `notes/outputs/`.

**Baseline for the log archive account**

4. Go to its baseline stack:
   ```bash
   cd terraform/live/log-archive/baseline
   ```
5. Create the backend file:
   ```bash
   cp backend.hcl.example backend.hcl
   ```
6. Open it:
   ```bash
   nano backend.hcl
   ```
   The file already holds two example lines. Replace them with the two lines that **step 1** printed for the log archive account, so that the file contains exactly these two lines, with your log archive account id in the bucket name:
   ```
   bucket  = "dpdp-tfstate-<log archive id>"
   profile = "dpdp-logarchive-admin"
   ```
   Each stack uses only the lines printed for its own account. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
7. Initialise:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
8. Prepare the plan. It must add three resources: the account-level S3 public access block, default EBS encryption, and an IAM Access Analyzer.
   ```bash
   terraform plan -out=b.tfplan
   ```
9. Apply it:
   ```bash
   terraform apply b.tfplan
   ```
10. Return to the workbench folder:
    ```bash
    cd ~/work/dpdp-on-aws-workbench
    ```

**Baselines for the workload and sandbox accounts**

11. Repeat steps 4 to 10 in `terraform/live/workload/baseline`. In step 6, use the two lines printed by **step 2**: the bucket `dpdp-tfstate-<workload id>` and the profile `dpdp-workload-eng`.
12. Repeat steps 4 to 10 in `terraform/live/sandbox/baseline`. In step 6, use the two lines printed by **step 3**: the bucket `dpdp-tfstate-<sandbox id>` and the profile `dpdp-sandbox-eng`.

**Check**

13. Public access block in the workload account; all four settings must be `true`:
    ```bash
    scripts/log_step.sh 6.13 "Public access block, workload account" -- \
      aws s3control get-public-access-block --account-id <workload id> \
      --profile dpdp-workload-eng
    ```
14. Default disk encryption in the workload account; it must print `true`:
    ```bash
    scripts/log_step.sh 6.14 "Default disk encryption, workload account" -- \
      aws ec2 get-ebs-encryption-by-default --profile dpdp-workload-eng
    ```
15. Log the three baselines:
    ```bash
    scripts/log_step.sh 6 \
      "Baselines applied in log archive, workload and sandbox: 3 resources each"
    ```

---

## Part 7. Logging and evidence

**Why:** Rule 6(1)(c) and Rule 6(1)(e) require access to personal data to be logged, and the logs kept for a year and protected. The organisation trail records every action in every account. The logs and the test evidence are kept in the log archive account under Object Lock, so nobody can delete or change them, including an administrator.

### 7.1 Log and evidence buckets (log archive account)

**Why:** These buckets are created first, because the trail in 7.2 and the tests in the Release 1 guide write into them.

1. Go to the logging stack:
   ```bash
   cd terraform/live/log-archive/logging
   ```
2. Create the backend file:
   ```bash
   cp backend.hcl.example backend.hcl
   ```
3. Open it and paste the log archive account's two lines (Part 6, step 1). Save and close.
   ```bash
   nano backend.hcl
   ```
4. Create the variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
5. Open it and set the management id, organisation id, workload id and sandbox id. Save and close.
   ```bash
   nano terraform.tfvars
   ```
6. Initialise:
   ```bash
   terraform init -backend-config=backend.hcl
   ```
7. Prepare the plan:
   ```bash
   terraform plan -out=log.tfplan
   ```

The plan adds three locked buckets, each with versioning, Object Lock, encryption, ownership controls, a public access block and a bucket policy (21 resources). Nothing is destroyed.

**Before applying, understand this:** objects in `dpdp-evidence-live-<id>` are in compliance mode. Nobody, including the root user, can delete them for 30 days, and the bucket cannot be deleted while they exist. The retention can later be extended but never shortened.

8. Apply the plan:
   ```bash
   terraform apply log.tfplan
   ```
9. Show the bucket names and save them in the bootstrap log. Part 7.2 and the Release 1 guide use them:
   ```bash
   ../../../../scripts/log_step.sh 7.1 "Log and evidence bucket names" -- \
     terraform output
   ```
10. Return to the workbench folder:
    ```bash
    cd ~/work/dpdp-on-aws-workbench
    ```

### 7.2 Organisation trail (management account)

**Why:** One trail, created in the management account, records actions in every account of the organisation and writes them to the log archive bucket.

1. Show the log bucket name saved in Part 7.1. Keep the `cloudtrail_bucket_name` value on screen for step 7.
   ```bash
   cat notes/outputs/*part-7.1.txt
   ```
2. Go to the trail stack:
   ```bash
   cd terraform/live/management/trail
   ```
3. Copy the backend file of the organisation stack. Both stacks are in the management account and use its state bucket; each keeps its own state file there.
   ```bash
   cp ../organization/backend.hcl backend.hcl
   ```
4. Check it. It must show the two lines `bucket = "dpdp-tfstate-<management id>"` and `profile = "dpdp-mgmt-admin"`.
   ```bash
   cat backend.hcl
   ```
5. Create the variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
6. Open it:
   ```bash
   nano terraform.tfvars
   ```
7. Replace the example bucket name with the `cloudtrail_bucket_name` value from step 1, so the line reads `cloudtrail_bucket_name = "dpdp-cloudtrail-logs-<log archive id>"`. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
8. Initialise. It must end with `Terraform has been successfully initialized!`.
   ```bash
   terraform init -backend-config=backend.hcl
   ```
9. Prepare the plan. It must read `Plan: 1 to add, 0 to change, 0 to destroy.`: the trail `dpdp-organization-trail`.
   ```bash
   terraform plan -out=trail.tfplan
   ```
10. Apply it:
    ```bash
    terraform apply trail.tfplan
    ```
11. Save the trail's ARN in the bootstrap log. The Release 1 tests use it.
    ```bash
    ../../../../scripts/log_step.sh 7.2 "Organisation trail ARN" -- terraform output
    ```
12. Return to the workbench folder:
    ```bash
    cd ~/work/dpdp-on-aws-workbench
    ```

### 7.3 Checks

**Why:** These checks confirm that the trail is running and the logs are locked before anything relies on them.

1. The trail is logging; it must print `true`:
   ```bash
   scripts/log_step.sh 7.3 "Organisation trail is logging" -- \
     aws cloudtrail get-trail-status --name dpdp-organization-trail \
     --profile dpdp-mgmt-admin --query IsLogging
   ```
2. The log bucket is locked; it must show `GOVERNANCE` and `365` days:
   ```bash
   scripts/log_step.sh 7.3 "Log bucket lock" -- \
     aws s3api get-object-lock-configuration \
     --bucket dpdp-cloudtrail-logs-<log archive id> --profile dpdp-logarchive-admin
   ```
3. Within about 15 minutes, log files appear in the trail bucket. This lists the first ten, which end in `.json.gz`. If it prints nothing, wait another 10 minutes and run it again.
   ```bash
   scripts/log_step.sh 7.3 "First log files delivered" -- bash -c \
     'aws s3 ls s3://dpdp-cloudtrail-logs-<log archive id>/AWSLogs/ --recursive \
     --profile dpdp-logarchive-admin | head'
   ```

---

## Part 8. Cost alerts

**Why:** An email reaches you while a mistake is still small, before it becomes a large bill.

### 8.1 Monthly budget (Terraform, management account)

1. Go to the cost stack:
   ```bash
   cd terraform/live/management/cost
   ```
2. Copy the backend file of the organisation stack, as in Part 7.2:
   ```bash
   cp ../organization/backend.hcl backend.hcl
   ```
3. Create the variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
4. Open it:
   ```bash
   nano terraform.tfvars
   ```
5. Replace `yourname@gmail.com` with the email address that should receive the alerts. Leave `monthly_budget_usd = 18` as it is. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**. The file is never committed, so the address stays private.
6. Initialise. It must end with `Terraform has been successfully initialized!`.
   ```bash
   terraform init -backend-config=backend.hcl
   ```
7. Prepare the plan. It must read `Plan: 1 to add, 0 to change, 0 to destroy.`: the budget `dpdp-monthly`.
   ```bash
   terraform plan -out=cost.tfplan
   ```
8. Apply it:
   ```bash
   terraform apply cost.tfplan
   ```
9. Return to the workbench folder:
   ```bash
   cd ~/work/dpdp-on-aws-workbench
   ```
10. Keep the management account id in a short value, `A`, for the next step:
    ```bash
    A=$(aws sts get-caller-identity --profile dpdp-mgmt-admin \
      --query Account --output text)
    ```
11. Log the budget. It must print `dpdp-monthly`, `18.0` and `USD`.
    ```bash
    scripts/log_step.sh 8.1 "Budget dpdp-monthly" -- \
      aws budgets describe-budgets --profile dpdp-mgmt-admin --account-id $A \
      --query "Budgets[].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit]" --output text
    ```

The budget is USD 18 a month for the whole organisation (about INR 1,500), with emails at one third, two thirds and the full amount, and when the forecast exceeds it.

12. **Console:** **Billing and Cost Management** → **Budgets** → `dpdp-monthly`. Save the screenshot `8-budget-alerts.png` of its alerts (Part 1.6), and log it:
    ```bash
    scripts/log_step.sh 8.1 \
      "Screenshot 8-budget-alerts.png: four alerts on dpdp-monthly"
    ```

### 8.2 Cost Anomaly Detection (console)

**Why:** The budget in 8.1 warns when the month's total grows. Anomaly detection warns when spending jumps in a way that does not fit the usual pattern, for example a forgotten resource, even while the month's total is still small.

All steps are in the management account, signed in through the access portal with `BreakGlassAdmin`.

1. Open **Billing and Cost Management**. In the left menu, open **Cost Explorer** once. This switches it on, which anomaly detection needs; its data can take up to 24 hours to appear.
2. In the left menu, choose **Cost Anomaly Detection**.
3. Open the **Cost monitors** tab and look at the list:
   - If it shows a monitor whose type is **AWS services** (AWS often creates one, named `Default-Services-Monitor`), keep it. Then open it and look at **Alert subscriptions** in its **Monitor details**:
     - If it has a subscription, usually `Default-Services-Subscription`, open it and check its **Threshold**. AWS sets it to `$100.00 AND 40.00%`, which is far too high for this build. Choose **Edit Subscription**, set the threshold as in step 5, item 6, choose **Remove** next to the percentage threshold so that only one is left, and choose **Save**. Then go to step 6.
     - If it has no subscription, go to step 5.
   - If the list is empty, do step 4.
4. **Only if the list was empty:** create a monitor with its subscription.
   1. Choose **Create monitor**.
   2. **Monitor method:** **Managed by AWS**. **Dimension:** **AWS services**.
   3. **Monitor name:** `dpdp-services-monitor`. Choose **Next**.
   4. **Alert subscription:** **Create a new subscription**, and fill it in as in step 5, items 3 to 6.
   5. Choose **Create monitor**, then go to step 6.
5. **If a monitor already existed:** add a subscription to it.
   1. Open the **Alert subscriptions** tab.
   2. Choose **Create a subscription**.
   3. **Subscription name:** `dpdp-daily-anomalies`.
   4. **Alerting frequency:** **Daily summaries**. These come by email. (**Individual alerts** would need an Amazon SNS topic, which this build does not use.)
   5. **Alert recipients:** the same email address as in Part 8.1.
   6. **Threshold:** `5` with **amount above expected spend** (AWS's documentation calls this an absolute threshold). The summary under it reads: "When the anomaly impact is $5.00 above the expected spend, you receive anomaly alerts."
   7. **Cost monitors:** tick the **AWS services** monitor from step 3.
   8. Choose **Create subscription**.
6. Log the subscription. Cost Anomaly Detection is answered only from US East (N. Virginia), so the command names that region. It must print the subscription's name (`dpdp-daily-anomalies`, or `Default-Services-Subscription` if you edited AWS's own) and `DAILY`.
   ```bash
   scripts/log_step.sh 8.2 "Cost Anomaly Detection subscription" -- \
     aws ce get-anomaly-subscriptions --region us-east-1 --profile dpdp-mgmt-admin \
     --query "AnomalySubscriptions[].[SubscriptionName,Frequency]" --output text
   ```

### 8.3 Commit the Terraform lock files

**Why:** Parts 4 to 8 ran `terraform init` in seven stacks, and each created a `.terraform.lock.hcl` file (see "Rules for every step"). Committing them fixes the AWS provider version for every later run, on this laptop and in the checks on GitHub.

1. List the lock files not yet in Git:
   ```bash
   git status
   ```
   Only `.terraform.lock.hcl` files may be listed. If any other file is listed, stop and find out why.
2. Create a branch:
   ```bash
   git checkout -b lock-files-$(date +%Y%m%d-%H%M)
   ```
3. Add the lock files:
   ```bash
   git add terraform/live/*/*/.terraform.lock.hcl
   ```
4. Commit:
   ```bash
   git commit -m "Add Terraform provider lock files"
   ```
5. Push the branch:
   ```bash
   git push -u origin HEAD
   ```
6. **Console (GitHub):** **Compare & pull request** → **Create pull request**. When all three checks are green: **Merge pull request**, with **Create a merge commit** → **Confirm merge** → **Delete branch**.
7. Return to main:
   ```bash
   git checkout main && git pull
   ```
8. Delete the branch on the laptop:
   ```bash
   git branch -d $(git branch --list "lock-files-*" --format="%(refname:short)")
   ```

**Check:** `git status` says `nothing to commit, working tree clean`.

---

## Part 9. Guardrails, in three stages

**Why:** Guardrails set limits that nobody in a member account can exceed, including its administrators. They are attached in stages, each followed by a test, so a faulty guardrail is found in the Sandbox before it can lock you out of the accounts that matter.

The guardrails are attached by editing one variable in `terraform/live/management/organization/terraform.tfvars` and applying. Each stage is followed by a test. **Recovery path:** guardrails never apply to the management account, so a faulty guardrail can always be detached from there with `dpdp-mgmt-admin`.

**How to apply a stage** (used in stages A, B and C):

1. Open the variables file:
   ```bash
   nano terraform/live/management/organization/terraform.tfvars
   ```
2. Each stage below (A, B and C) has a **File content** box: the whole `scp_attachments` block as it must look after that stage. Each stage changes one line of the block, and the lines of earlier stages stay as they are:

   | Stage | Line that changes |
   |---|---|
   | A | `sandbox   = ["region", "baseline", "cost"]` |
   | B | `workloads = ["region", "baseline", "buckets", "cost"]` |
   | C | `security  = ["region", "baseline", "buckets"]` |

   Move the cursor with the arrow keys to that line, replace its `[]` with the list shown, and check that the whole block matches the stage's **File content** box. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
3. Go to the organisation stack:
   ```bash
   cd terraform/live/management/organization
   ```
4. Prepare the plan. It must add only the stage's attachments and change or destroy nothing: `Plan: 3 to add, 0 to change, 0 to destroy.` for stage A, `4 to add` for stage B, and `3 to add` for stage C. If it reads anything else, stop.
   ```bash
   terraform plan -out=org.tfplan
   ```
5. Apply it:
   ```bash
   terraform apply org.tfplan
   ```
6. Return to the workbench folder:
   ```bash
   cd ~/work/dpdp-on-aws-workbench
   ```

### Stage A: Sandbox

**File content** for `scp_attachments` (3 attachments to add):

```hcl
scp_attachments = {
  sandbox   = ["region", "baseline", "cost"]
  workloads = []
  security  = []
}
```

**Test stage A** (with `dpdp-sandbox-eng`):

1. Try to create a bucket in Singapore. It **must fail** with `AccessDenied` and a message mentioning a service control policy. The log records the refusal as the evidence.
   ```bash
   scripts/log_step.sh 9.A "Sandbox: bucket in Singapore must be refused" -- \
     aws s3api create-bucket --bucket dpdp-stage-a-$RANDOM --region ap-southeast-1 \
     --create-bucket-configuration LocationConstraint=ap-southeast-1 \
     --profile dpdp-sandbox-eng
   ```
2. Choose a name for a test bucket in Mumbai:
   ```bash
   B=dpdp-stage-a-ok-$RANDOM
   ```
3. Create it. This **must work**.
   ```bash
   scripts/log_step.sh 9.A "Sandbox: bucket in Mumbai must be allowed" -- \
     aws s3api create-bucket --bucket $B --region ap-south-1 \
     --create-bucket-configuration LocationConstraint=ap-south-1 \
     --profile dpdp-sandbox-eng
   ```
4. Remove it:
   ```bash
   aws s3api delete-bucket --bucket $B --profile dpdp-sandbox-eng
   ```

Both results are saved in the bootstrap log by steps 1 and 3.

### Stage B: Workloads (only after Part 7 is complete)

**File content** for `scp_attachments` (4 attachments to add):

```hcl
scp_attachments = {
  sandbox   = ["region", "baseline", "cost"]
  workloads = ["region", "baseline", "buckets", "cost"]
  security  = []
}
```

**Test stage B:** repeat the four test steps of stage A with `--profile dpdp-workload-eng` in place of `--profile dpdp-sandbox-eng`, and `9.B "Workloads: …"` in place of `9.A "Sandbox: …"` in the log notes.

### Stage C: Security

**File content** for `scp_attachments` (3 attachments to add):

```hcl
scp_attachments = {
  sandbox   = ["region", "baseline", "cost"]
  workloads = ["region", "baseline", "buckets", "cost"]
  security  = ["region", "baseline", "buckets"]
}
```

From this moment, the log and evidence buckets can no longer be deleted or weakened by anyone in the member accounts.

**Test stage C** (with `dpdp-logarchive-admin`, the most powerful role in that account):

1. Set the bucket name:
   ```bash
   B=dpdp-cloudtrail-logs-<log archive id>
   ```
2. Pick the first log file in it. The query keeps only real log files: names that end in `.json.gz` inside a folder named `CloudTrail`. It skips folder entries and digest files.
   ```bash
   K=$(aws s3api list-objects-v2 --bucket $B --prefix AWSLogs/ --no-paginate \
     --output text --profile dpdp-logarchive-admin \
     --query "Contents[?contains(Key,'/CloudTrail/') && ends_with(Key,'.json.gz')]|[0].Key")
   ```
   Check it. It must print a path that contains `/CloudTrail/` and ends in `.json.gz`:
   ```bash
   echo "$K"
   ```
3. Try to delete that log file. It **must fail** with `AccessDenied`.
   ```bash
   scripts/log_step.sh 9.C "Log file deletion must be refused" -- \
     aws s3api delete-object --bucket $B --key "$K" --profile dpdp-logarchive-admin
   ```
4. Try to delete the bucket. It **must fail** with `AccessDenied`.
   ```bash
   scripts/log_step.sh 9.C "Log bucket deletion must be refused" -- \
     aws s3api delete-bucket --bucket $B --profile dpdp-logarchive-admin
   ```

The full set of these tests runs automatically in the Release 1 guide (tests T5 and T6).

### Changing a protected bucket later

**What the `buckets` guardrail blocks.** Since stage C, the `buckets` guardrail sits on the Security unit, which holds the log archive and audit accounts. Nobody in those accounts can change the log and evidence buckets: not `BreakGlassAdmin`, and not Terraform running as `BreakGlassAdmin`. The guardrail refuses:

- deleting a log or evidence file, or a version of one, and deleting a bucket;
- going around the lock (`BypassGovernanceRetention`) or changing it;
- switching off versioning, and adding or changing lifecycle rules;
- changing or deleting a bucket policy;
- changing encryption, ownership, access control lists or the public access block;
- adding replication.

**Why this needs a procedure.** That protection is the point of the guardrail. It also means that a later release with a legitimate reason to change one of these settings is refused in the same way: for example, when a new reader has to be added to a bucket policy, or a retention period has to be made longer. A release that needs such a change says so in its guide and refers to this procedure. Until then, nothing here is done.

**Where it can be lifted.** Only from the management account, because guardrails never apply there. It is done with the organisation stack and the same `terraform.tfvars` as stages A to C, and only for the minutes the change takes.

**Where the change itself comes from.** You never edit the bucket code by hand. The release that needs the change ships it as a starter kit update: new versions of files in `terraform/live/log-archive/logging/` or `terraform/modules/locked-bucket/`, listed in `KIT_CHANGES.md` together with what changes in AWS. For example, a release that lets the audit account read the evidence bucket would ship a new bucket policy; its plan would show `aws_s3_bucket_policy` as `will be updated in-place`. Applying the kit update puts the new code in the workbench but changes nothing in AWS; the steps below then apply it.

**Procedure**

1. Apply the release's kit update (Part 1.5). The new code is now in the workbench and in Git; nothing has changed in AWS yet. Read the version's entry in `KIT_CHANGES.md` and note what it says will change in AWS: step 10 checks the plan against it.
2. Record why the change is needed, before anything is changed in AWS:
   ```bash
   scripts/log_step.sh 9 \
     "Decision: lift buckets guardrail from Security for <the change and its reason>"
   ```
3. Open the variables file:
   ```bash
   nano terraform/live/management/organization/terraform.tfvars
   ```
4. Change the `security` line from `["region", "baseline", "buckets"]` to the following, leaving the other lines as they are. Save with **Ctrl+O**, Enter, and close with **Ctrl+X**.
   ```
   security  = ["region", "baseline"]
   ```
5. Go to the organisation stack:
   ```bash
   cd terraform/live/management/organization
   ```
6. Prepare the plan. It must read `Plan: 0 to add, 0 to change, 1 to destroy.`: the one attachment of `buckets` to the Security unit. This is the only plan in this guide where a destroy is expected; if anything else is listed, stop.
   ```bash
   terraform plan -out=org.tfplan
   ```
7. Apply it:
   ```bash
   terraform apply org.tfplan
   ```
8. Log it:
   ```bash
   ../../../../scripts/log_step.sh 9 "buckets guardrail detached from Security"
   ```
9. Go to the logging stack:
   ```bash
   cd ~/work/dpdp-on-aws-workbench/terraform/live/log-archive/logging
   ```
10. Prepare the plan. It must show only the change named in the `KIT_CHANGES.md` entry of step 1, and nothing to destroy. If it shows anything else, stop and run steps 12 to 16 to put the guardrail back before looking into it.
   ```bash
   terraform plan -out=log.tfplan
   ```
11. Apply it, and log it:
    ```bash
    terraform apply log.tfplan
    ```
    ```bash
    ../../../../scripts/log_step.sh 9 "Protected bucket change applied: <the change>"
    ```
12. Go back to the organisation stack:
    ```bash
    cd ~/work/dpdp-on-aws-workbench/terraform/live/management/organization
    ```
13. Open the variables file again and restore the `security` line. Save and close.
    ```bash
    nano terraform.tfvars
    ```
    ```
    security  = ["region", "baseline", "buckets"]
    ```
14. Prepare the plan. It must read `Plan: 1 to add, 0 to change, 0 to destroy.`
    ```bash
    terraform plan -out=org.tfplan
    ```
15. Apply it, and log it:
    ```bash
    terraform apply org.tfplan
    ```
    ```bash
    ../../../../scripts/log_step.sh 9 "buckets guardrail attached to Security again"
    ```
16. Return to the workbench folder:
    ```bash
    cd ~/work/dpdp-on-aws-workbench
    ```
17. Prove the protection is back: run test stage C again, steps 1 to 4. Both attempts must fail with `AccessDenied`, as before.
18. Save the trail's record of the detach and the re-attach. Changes to the organisation are recorded in US East (N. Virginia). Each command asks the trail for one event by name; a plain list of recent events is not enough, because every Terraform plan adds many read events that push the detach out of view. The trail can take up to 15 minutes to show an event, so run these a little after step 15.

    The detach. It must show a `DetachPolicy` with its time and your user:
    ```bash
    scripts/log_step.sh 9 "Trail record of the guardrail detach" -- \
      aws cloudtrail lookup-events --region us-east-1 --profile dpdp-mgmt-admin \
      --lookup-attributes AttributeKey=EventName,AttributeValue=DetachPolicy \
      --max-results 5 --output text --query "Events[].[EventTime,EventName,Username]"
    ```
    The re-attach. It must show an `AttachPolicy` later than the detach; older ones, from stages A to C, may be listed below it:
    ```bash
    scripts/log_step.sh 9 "Trail record of the guardrail re-attach" -- \
      aws cloudtrail lookup-events --region us-east-1 --profile dpdp-mgmt-admin \
      --lookup-attributes AttributeKey=EventName,AttributeValue=AttachPolicy \
      --max-results 5 --output text --query "Events[].[EventTime,EventName,Username]"
    ```
    The two times show how long the guardrail was off.

`terraform.tfvars` is not committed; after step 13 it is back as it was before step 4. The code change was committed with the kit update in step 1, so nothing else needs committing.

**Why the change is itself evidence.** The organisation trail records every step with its time and the identity that took it: the detach (`DetachPolicy`), the change to the bucket (for example `PutBucketPolicy`, recorded in the log archive account), and the re-attach (`AttachPolicy`). Together with the bootstrap log, which gives the reason, an auditor can see that the protection was lifted only for the minutes the change took, by whom and for what purpose, and that it was restored and tested afterwards.

---

## Part 10. GitHub settings

**Why:** The public repository is what readers see and copy. These settings make sure every change arrives through a pull request, carries a signature, cannot erase history, and cannot publish a key by mistake.

### 10.1 Public repository `dpdp-on-aws`

1. **Settings → General → Pull Requests:** tick only **Allow merge commits**. Untick squash merging and rebase merging. Tick **Automatically delete head branches**.
2. **Settings → Rules → Rulesets → New branch ruleset:**
   - Name `protect-main`, enforcement **Active**, target branch: **Include default branch**
   - Tick **Restrict deletions**, **Block force pushes**, **Require signed commits**
   - Tick **Require a pull request before merging** with required approvals **0**
   - Leave **Require status checks to pass** unticked for now. A check can be selected only after it has run once; the Release 1 guide, Step 9, adds it after the first pull request
3. **Settings → Actions → General:**
   - **Approval for running fork pull request workflows from contributors:** **Require approval for all external contributors**
   - **Workflow permissions:** **Read repository contents and packages permissions**
4. **Settings → Advanced Security:** confirm secret scanning and push protection are on.

### 10.2 Private workbench `dpdp-on-aws-workbench`

Branch rules are not enforced on private repositories on GitHub's free plan. The pre-commit hooks installed in Part 1.4 run the secret scan, the formatting check and the register check before every commit.

### 10.3 Checkpoint

**Why:** This confirms the platform is complete before the Release 1 guide builds on it. Every check reads the current state from AWS or GitHub and saves the result in the bootstrap log, so the log shows the platform as it stood on the day the build moved on to Release 1.

Run every step from the workbench folder, signed in:
```bash
cd ~/work/dpdp-on-aws-workbench && source .venv/bin/activate
```
```bash
aws sso login --sso-session dpdp
```

**1. Accounts in their units.** This is one command over several lines; paste it as it is.
```bash
scripts/log_step.sh 10.3 "Accounts in each unit" -- bash -c '
P="--profile dpdp-mgmt-admin --output text"
R=$(aws organizations list-roots $P --query "Roots[0].Id")
echo "Root: $(aws organizations list-accounts-for-parent --parent-id $R $P \
  --query "Accounts[].Name")"
for ou in $(aws organizations list-organizational-units-for-parent --parent-id $R \
  $P --query "OrganizationalUnits[].Id"); do
  n=$(aws organizations describe-organizational-unit --organizational-unit-id $ou \
    $P --query OrganizationalUnit.Name)
  echo "$n: $(aws organizations list-accounts-for-parent --parent-id $ou $P \
    --query "Accounts[].Name")"
done'
```
It must print four lines, in any order:

| Line | Accounts, in any order |
|---|---|
| `Root:` | The management account, your project account, `Identity Delegated Admin` |
| `Security:` | `dpdp-log-archive`, `dpdp-audit` |
| `Workloads:` | `dpdp-workload` |
| `Sandbox:` | `dpdp-sandbox` |

**2. Sign-in only through Identity Center.** The five profiles, as in Part 5.2. Each line must show the right account and an `Arn` with `AWSReservedSSO_`:
```bash
scripts/log_step.sh 10.3 "Five profile checks" -- bash -c \
  'for p in dpdp-logarchive-admin dpdp-logarchive-auditor dpdp-workload-eng \
  dpdp-workload-admin dpdp-sandbox-eng; do echo "$p: $(aws sts get-caller-identity \
  --profile $p --query Arn --output text)"; done'
```

**3. No IAM users** in the workload and log archive accounts. Both lines must end empty: no user names.
```bash
scripts/log_step.sh 10.3 "No IAM users in workload and log archive" -- bash -c \
  'for p in dpdp-workload-admin dpdp-logarchive-admin; do echo "$p: $(aws iam \
  list-users --profile $p --query "Users[].UserName" --output text)"; done'
```

**4. Root credentials managed centrally.** It must list `RootCredentialsManagement` and `RootSessions`. That the four member accounts have no root credentials is shown by the screenshot from Part 5.3.
```bash
scripts/log_step.sh 10.3 "Central root access management enabled" -- \
  aws iam list-organizations-features --profile dpdp-mgmt-admin
```

**5. Organisation trail running.** It must print `true`:
```bash
scripts/log_step.sh 10.3 "Organisation trail is logging" -- \
  aws cloudtrail get-trail-status --name dpdp-organization-trail \
  --profile dpdp-mgmt-admin --query IsLogging
```

**6. Logs locked for 365 days.** Replace `<log archive id>`. It must show `"Mode": "GOVERNANCE"` and `"Days": 365`:
```bash
scripts/log_step.sh 10.3 "Log bucket lock" -- \
  aws s3api get-object-lock-configuration \
  --bucket dpdp-cloudtrail-logs-<log archive id> --profile dpdp-logarchive-admin
```

**7. Guardrails attached, read from AWS.** This asks AWS which guardrails are attached to each unit. This is one command over several lines; paste it as it is.
```bash
scripts/log_step.sh 10.3 "Guardrails attached to each unit, read from AWS" -- bash -c '
P="--profile dpdp-mgmt-admin --output text"
R=$(aws organizations list-roots $P --query "Roots[0].Id")
for ou in $(aws organizations list-organizational-units-for-parent --parent-id $R \
  $P --query "OrganizationalUnits[].Id"); do
  n=$(aws organizations describe-organizational-unit --organizational-unit-id $ou \
    $P --query OrganizationalUnit.Name)
  echo "$n: $(aws organizations list-policies-for-target --target-id $ou \
    --filter SERVICE_CONTROL_POLICY $P --query "Policies[].Name")"
done'
```
It must print three lines. Besides `FullAWSAccess`, which AWS attaches to every unit, each unit must have exactly these guardrails, in any order:

| Unit | Guardrails |
|---|---|
| `Security:` | `dpdp-deny-regions-outside-mumbai`, `dpdp-baseline-protections`, `dpdp-protect-log-and-evidence-buckets` |
| `Workloads:` | `dpdp-deny-regions-outside-mumbai`, `dpdp-baseline-protections`, `dpdp-protect-log-and-evidence-buckets`, `dpdp-deny-costly-services` |
| `Sandbox:` | `dpdp-deny-regions-outside-mumbai`, `dpdp-baseline-protections`, `dpdp-deny-costly-services` |

**8. Guardrails as Terraform records them.** A cross-check of step 7: the list of attachments in the organisation stack's state, each named `<unit>-<guardrail>`. First go to the stack:
```bash
cd terraform/live/management/organization
```
Save the list:
```bash
../../../../scripts/log_step.sh 10.3 "Guardrail attachments in Terraform state" -- \
  terraform output attached_guardrails
```
It must list these 10 entries, which match step 7 unit by unit:
```
"sandbox-baseline", "sandbox-cost", "sandbox-region",
"security-baseline", "security-buckets", "security-region",
"workloads-baseline", "workloads-buckets", "workloads-cost", "workloads-region"
```
Return to the workbench folder:
```bash
cd ~/work/dpdp-on-aws-workbench
```

**9. Budget.** Keep the management account id in `A`:
```bash
A=$(aws sts get-caller-identity --profile dpdp-mgmt-admin \
  --query Account --output text)
```
It must print `dpdp-monthly`, `18.0` and `USD`:
```bash
scripts/log_step.sh 10.3 "Budget" -- \
  aws budgets describe-budgets --profile dpdp-mgmt-admin --account-id $A \
  --query "Budgets[].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit]" --output text
```

**10. Anomaly alerts.** It must print your subscription's name and `DAILY`:
```bash
scripts/log_step.sh 10.3 "Cost Anomaly Detection subscription" -- \
  aws ce get-anomaly-subscriptions --region us-east-1 --profile dpdp-mgmt-admin \
  --query "AnomalySubscriptions[].[SubscriptionName,Frequency]" --output text
```

**11. GitHub rules on the public repository (console).** Open `dpdp-on-aws` → **Settings** → **Rules** → **Rulesets**. `protect-main` must show **Active**. Open it and check the rules from Part 10.1, step 2. Save the screenshot `10.3-ruleset-protect-main.png` (Part 1.6), and log it:
```bash
scripts/log_step.sh 10.3 \
  "Screenshot 10.3-ruleset-protect-main.png: protect-main Active"
```

**12. Workbench clean.** It must say `nothing to commit, working tree clean`. If `.terraform.lock.hcl` files are listed, commit them as in Part 8.3 first.
```bash
git status
```

**13. Back up the notes:**
```bash
cp -r -u notes/. "/mnt/c/Users/<windows user>/OneDrive/dpdp-bootstrap-notes/"
```

When all thirteen steps give the results described, the platform is complete. Log it, and continue with the **Release 1 Build Guide, Step 1**.
```bash
scripts/log_step.sh 10.3 "Checkpoint complete; platform ready for Release 1"
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Token has expired` or `SSO session ... expired` | Run `aws sso login --sso-session dpdp` again |
| The **Secrets and misconfiguration scan** check fails within seconds, with `unable to find version 0.28.0` | The workbench has a `checks.yml` from before the kit update of 22 October 2026 (third update). The old trivy-action tags were taken over by an attacker in March 2026 and then deleted. Apply that kit update (Part 1.5) |
| The **Secrets** step of that check fails with `Resource not accessible by integration` (HTTP 403) | gitleaks may not read the pull request. The same kit update adds `pull-requests: read` to the job (Part 1.5) |
| `git status` lists `.terraform.lock.hcl` files | Expected after `terraform init`. They are committed in Part 8.3, or with a kit update (Part 1.5, step 4) |
| `pip install` times out, or the connection is reset, while downloading from `files.pythonhosted.org` | The internet connection cannot reach Python's download server. Try once with `pip install --no-cache-dir --timeout 120 -r requirements.txt`. If it fails again, download the package file over another connection, such as a phone hotspot, and install it with `pip install <file>.whl` |
| A step fails with "account verification is in progress" | AWS has not finished verifying the new account. It can take up to two days. Wait, then retry the step |
| IAM Identity Center console shows no instance | The console is in the wrong region. Switch to the Primary Region (normally US East, N. Virginia) |
| `aws sso login` fails with an invalid start URL or region | `sso_start_url` and `sso_region` in `~/.aws/config` must match IAM Identity Center → Settings (Part 3.3) |
| `aws sso login` reports "Identity Center instance that does not exist or does not exist in this region" | `sso_start_url` holds the IPv4-only portal link. Replace it with the Dual-stack link, ending in `.app.aws` (Part 3.5, step 5) |
| `aws sso login` prints `gio: ... Operation not supported` | Ubuntu in WSL cannot open the Windows browser. Copy the printed link into the Windows browser (Part 3.5, step 6), or install `wslu` as shown there |
| Your user is not in the Users tab when assigning access | Your Builder ID is not yet a user of the instance. In IAM Identity Center → Users, invite your Builder ID email, accept the invitation, then assign again |
| IAM Identity Center has no **Multi-account permissions** section in the left menu | Multi-account permissions are switched off. Part 3.4, first block: Settings → Management → Enable |
| Any action in a DPDP account in Mumbai is refused by a service control policy that is not one of the four in this guide | An AWS guardrail with `RegionFloor` is attached to Root. Go back to Part 3.2 |
| `terraform init`: bucket does not exist | Run `scripts/bootstrap_state_bucket.sh` for that account's profile and copy the printed lines into `backend.hcl` |
| Plan wants to destroy the organisation or an account | Stop. Check `organization_id` in `terraform.tfvars` and that you are in the right folder. `prevent_destroy` blocks the apply in any case |
| `ConstraintViolationException: You have exceeded the allowed number of AWS accounts` | A new organisation can start with an account limit below AWS's usual 10, and the organisation already holds three accounts. In the management account, region **US East (N. Virginia)**: **Service Quotas** → **AWS services** → **AWS Organizations** → **Default maximum number of accounts** → **Request increase at account level**, value **10**. This opens a request to AWS. When it is approved, run Part 4.2 steps 7 and 8 again: the plan then shows only the 4 accounts still to be created |
| Account creation still in progress after 30 minutes | Check the account emails for verification messages; wait up to an hour |
| `AccessDenied` when changing a protected bucket after stage C | Expected. Use Part 9, "Changing a protected bucket later" |
| Region test succeeds in stage A | The `region` guardrail is not attached to the unit that holds the account. Check `terraform output attached_guardrails` |
| A pull request check fails on formatting | Run `terraform fmt -recursive terraform` and commit |
| The budget page shows USD | AWS Budgets is set in US dollars; USD 18 is about INR 1,500 |
| `git clone` or `git push` asks for a password | The access key from Part 1.3, steps 12 to 15, is missing or not added to GitHub as an **Authentication key** |
| `unzip: cannot find` the starter kit | Check the Windows path in Part 1.4, step 4. In Ubuntu, Windows drives are under `/mnt/c` |
