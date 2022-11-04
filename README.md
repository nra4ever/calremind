# CalRemind
![screenshot of generated sensor in HA developer tools](https://github.com/nra4ever/calremind/raw/main/sensor.png)
A sensor based system to facilitate processing and displaying upcoming calendar events.

## Installation

Download the `calremind` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `calremind` module.

## App configuration

```yaml
hacs:
    module: calremind
    class: calremind
    server_ip: "192.168.1.122"
    ha_port: "8123"
    ha_token: "your HA token goes here"
    calendar_id: calendar.work
    max_events: 3
    hours_away: 48
    sensor_id: "sensor.calremind"
    index_offset: 0
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module`   | False | string | | The module name of the app.
`class`    | False | string | | The name of the Class.
`server_ip`| False | string | | the IP of the Home Assistant Installation.
`ha_port`  | True  | string | `8123` | The Port of the Home Assistant Installation.
`ha_token` | False | string | | A Long Lived Access Token for HA.
`calendar_id`| False | string | | The ID of the Calendar to Track Upcoming Events for.
`max_events`| True | integer | `3` | Amount of Upcoming Events to Track at Once.
`hours_away`| True | integer | `48` | Amount of Hours to Look Ahead for Events.
`sensor_id` | True | string | `sensor.calremind` | The Entity ID for the Published Sensor.
`index_offset` | True | integer | `0` | Offset for Sensor Attribute Numbering
