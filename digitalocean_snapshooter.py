#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""DigitalOcean Snapshooter.

Usage:
  digitalocean_snapshooter.py droplet list
  digitalocean_snapshooter.py droplet destroy <droplet_id>
  digitalocean_snapshooter.py snapshot take <droplet_id>
  digitalocean_snapshooter.py snapshot check <snapshot_id>
  digitalocean_snapshooter.py snapshot restore <droplet_id> <snapshot_id>
  digitalocean_snapshooter.py snapshot list <droplet_id>
  digitalocean_snapshooter.py (-h | --help)
  digitalocean_snapshooter.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""

__version__ = '0.0.1'

import os
from datetime import datetime
import asyncio
import digitalocean
from docopt import docopt
from yaspin import yaspin

personal_access_token = os.environ['DIGITALOCEAN_ACCESS_TOKEN']

manager = digitalocean.Manager(token=personal_access_token)


async def shutdown_droplet(droplet):
    if droplet.status == "off":
        return
    with yaspin(text=f'Shutting down {droplet.name}') as spinner:
        shutdown = droplet.shutdown(return_dict=False)
        while shutdown.status == "in-progress":
            await asyncio.sleep(15)
            shutdown = droplet.get_action(shutdown.id)
        if shutdown.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'shutdown_droplet failed: {shutdown.status}')
        spinner.ok("\u2714")
        return shutdown


async def snapshot_droplet(droplet):
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    snapshot = f'{droplet.name}-{timestamp}'
    with yaspin(text=f'Taking snapshot of {droplet.name}: {snapshot}') as spinner:
        action = droplet.take_snapshot(snapshot, return_dict=False)
        while action.status == "in-progress":
            await asyncio.sleep(30)
            action = droplet.get_action(action.id)
        if action.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'snapshot_droplet failed: {action.status}')
        spinner.ok("\u2714")
        return action


async def turnon_droplet(droplet):
    with yaspin(text=f'Turning on {droplet.name}') as spinner:
        action = droplet.power_on(return_dict=False)
        while action.status == "in-progress":
            await asyncio.sleep(15)
            action = droplet.get_action(action.id)
        if action.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'turnon_droplet failed: {action.status}')
        spinner.ok("\u2714")
        return action


def choose_size_slug(sizes, min_size, region):
    sizes = [size for size in sizes if size.disk >=
             min_size and region in size.regions]
    sizes = sorted(sizes, key=lambda size: size.price_hourly)
    return sizes[0].slug


async def check_snapshot(snapshot_id, region='fra1'):
    print(f'Sanity checking snapshot {snapshot_id}')
    snapshot = manager.get_image(snapshot_id)
    sizes = manager.get_all_sizes()
    size_slug = choose_size_slug(sizes, snapshot.min_disk_size, region)

    droplet = await create_droplet(
        name=f'{snapshot.name}-check',
        image_id=snapshot_id,
        size_slug=size_slug,
        region=region,
        tags=["snapshot_restore"])

    # todo: run tests
    await destroy_droplet(droplet)


async def create_droplet(**kwargs):
    name = kwargs['name']
    image_id = kwargs['image_id']
    size_slug = kwargs['size_slug']
    droplet = digitalocean.Droplet(token=personal_access_token,
                                   name=name,
                                   region=kwargs['region'],
                                   image=image_id,
                                   size_slug=size_slug,
                                   monitoring=True,
                                   tags=kwargs['tags'])
    msg = f'Creating new droplet {name} ({size_slug}) from snapshot {image_id}'
    with yaspin(text=msg) as spinner:
        droplet.create()
        create_action_id = droplet.action_ids[0]
        action = droplet.get_action(create_action_id)
        while action.status == "in-progress":
            await asyncio.sleep(15)
            action = droplet.get_action(action.id)
        if action.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'create_droplet failed: {action.status}')
        spinner.ok("\u2714")
        return droplet


async def rebuild_droplet(droplet, snasphot_id):
    with yaspin(text=f'Rebuilding droplet {droplet.name} from snapshot {snasphot_id}') as spinner:
        action = droplet.rebuild(snasphot_id, return_dict=False)
        while action.status == "in-progress":
            await asyncio.sleep(15)
            action = droplet.get_action(action.id)
        if action.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'rebuild failed: {action.status}')
        spinner.ok("\u2714")
        return action


async def destroy_droplet(droplet):
    print(f'Destroying droplet {droplet.name}')
    destroyed = droplet.destroy()
    print('Done') if destroyed else print('Droplet destruction failed')


async def restore_snapshot(droplet_id, snapshot_id):
    droplet = manager.get_droplet(droplet_id)
    with yaspin(text=f'Restoring {droplet.name} from snapshot {snapshot_id}') as spinner:
        action = droplet.restore(snapshot_id, return_dict=False)
        while action.status == "in-progress":
            await asyncio.sleep(15)
            action = droplet.get_action(action.id)
        if action.status == 'errored':
            spinner.fail("\u203C")
            raise RuntimeError(f'restore_snapshot failed: {action.status}')
        spinner.ok("\u2714")
        return action


async def take_snapshot(droplet_id):
    droplet = manager.get_droplet(droplet_id)
    await shutdown_droplet(droplet)
    await snapshot_droplet(droplet)
    # await check_snapshot(snapshot.id)
    await turnon_droplet(droplet)


def list_snapshots(droplet_id):
    droplet = manager.get_droplet(droplet_id)
    for snapshot_id in droplet.snapshot_ids:
        snapshot = manager.get_image(snapshot_id)
        print(
            f'{snapshot.name} ({snapshot.id}): {snapshot.size_gigabytes} GB (status: {snapshot.status})')


def list_droplets():
    droplets = manager.get_all_droplets()
    for droplet in droplets:
        print(f'{droplet.name} ({droplet.ip_address}): {droplet.id}')
    return droplets


async def main(args):
    if args["snapshot"] and args["take"]:
        await take_snapshot(args["<droplet_id>"])
    if args["snapshot"] and args["check"]:
        await check_snapshot(args["<snapshot_id>"])
    if args["snapshot"] and args["restore"]:
        await restore_snapshot(args["<droplet_id>"], args["<snapshot_id>"])
    if args["snapshot"] and args["list"]:
        list_snapshots(args["<droplet_id>"])
    if args["droplet"] and args["list"]:
        list_droplets()
    if args["droplet"] and args["destroy"]:
        droplet = manager.get_droplet(args["<droplet_id>"])
        await destroy_droplet(droplet)

if __name__ == '__main__':
    args = docopt(__doc__, version='DigitalOcean Snapshooter 1.0')
    asyncio.run(main(args))
