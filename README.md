### Target Mac setup

#### Enable SSH access

Navigate to `System Settings / General / Sharing` and turn on the `Remote Login` toggle under `Advanced`.

#### Create an SSH key

On your source computer, create a new key pair:
```bash
ssh-keygen -C "some@key-id.local"
```

Specify a full path to the key, e.g., `/Users/myuser/.ssh/source-computer`

#### Copy the public key to the destination mac

From the source computer:

```bash
ssh-copy-id -i ~/.ssh/source-computer.pub remote_username@remote_host
```

#### Optional - update the `~/.ssh/config` file

Add the following to your `config` file:

```
Host my-remote-mac
    HostName 192.168.1.100  # or a DNS name like remote.local
    User remote_username
    PreferredAuthentications publickey
    IdentityFile ~/.ssh/source-computer  # path to your private key
```