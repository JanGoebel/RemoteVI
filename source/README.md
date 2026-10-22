# source/

The LabVIEW toolkit. It's empty until the VIs are created in LabVIEW 2020, following [docs/labview-implementation.md](../docs/labview-implementation.md).

Layout once populated:

```
source/
├── RemoteVI.lvlib          the library (namespace, access scope: only API/ is public)
├── API/                    RemoteVI Publish.vi, RemoteVI Unpublish.vi, RemoteVI Get URL.vi, RemoteVI Options.ctl
├── Server/  Session/       Server.lvclass, Session.lvclass
├── Transport/              Transport.lvclass (abstract), TcpWebSocketTransport.lvclass, HTTP_*, WS_*, SHA1, Base64
├── Capture/                Panel Capture, Tile Grid/Diff, Encode Tile, QOI Encode, Frame Encode
├── Panel/                  PanelModel.lvclass, Classify Control
├── Input/                  ControlAdapter.lvclass + one child per control kind, Input Dispatcher
└── Tools/                  Tools-menu dialog (installs to <LabVIEW>/project/RemoteVI)
```

The project's `source` folder is auto-populating, so new files show up in `RemoteVI.lvproj` on their own.
