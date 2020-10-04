# reflexd

Automate your torrent client based on the filesystem.

reflexd enables you to write policies for auto-adding torrent files to a [Deluge] server when they are created.
There's no need to fumble with a client when you can configure directories ahead of time to do the write thing when a torrent file is saved there.
The intent is that you'd use this with a separate tool to automatically download files to whatever directories you want.

Features include:

* Declarative YAML config file
* Recursive directory watching
* `FILE` and `FILE_PARENT` variables for templating directories
* Hot config reloading

[Deluge]: https://deluge-torrent.org

## Demo

```
$ cat ~/.reflexd/config.yaml
reflexd:
  v1:
    directories:
      - path: "/downloads/Airing"
        recursive: true
        options:
          add_paused: true
          download_location: "{FILE_PARENT}" # dir where the file was created
          # remove the torrent immediately after completion
          remove_at_ratio: true
          stop_at_ratio: true
          stop_ratio: 0.0
$ docker run -v $HOME/.reflexd:/etc/reflexd:ro -v $HOME/Downloads:/downloads:rw quay.io/jzelinskie/reflexd:latest
```

## Developers

This project is fairly alpha and is mostly to scratch my own itch because I hate [flexget].
As a result, there's plenty of low hanging fruit when it comes to UX.
I've started another prototype of this project in Rust, because the [notify crate] is excellent, but I ended up getting this Python version usable really quick.


[flexget]: https://flexget.com
[notify crate]: https://crates.io/crates/notify
