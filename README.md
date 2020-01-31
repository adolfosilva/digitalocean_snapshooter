# digitalocean_snapshooter.py

You need Python 3 installed in your system.

Run:

```bash
$ pip install --user -r requirements.txt

$ DIGITALOCEAN_ACCESS_TOKEN=foobar ./digitalocean_snapshooter.py --help`

Usage:
  digitalocean_snapshooter.py droplet list
  digitalocean_snapshooter.py droplet destroy <droplet_id>
  digitalocean_snapshooter.py snapshot take <droplet_id>
  digitalocean_snapshooter.py snapshot check <snapshot_id>
  digitalocean_snapshooter.py snapshot restore <droplet_id> <snapshot_id>
  digitalocean_snapshooter.py snapshot list <droplet_id>
  digitalocean_snapshooter.py (-h | --help)
  digitalocean_snapshooter.py --version
```
