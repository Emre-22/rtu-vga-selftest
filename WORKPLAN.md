# Ownership

Coordinator:/root. New independent repository; original phone/game repositories stay intact.

| Work | Owner | Write paths | Status |
| --- | --- | --- | --- |
| RTL, metadata, workflows,README, integration/Git | /root | all except worker paths below | integrated; CI pending |
| Automated timing/animation tests and RTL frame images | /root/flight_game | test/ | complete; ownership released |
| Temporary SDK startup helper and tests | /root/flight_platform | fpga/ | complete; ownership released |

Workers report changes, checks, blockers and release ownership. No worker Git mutations. This test has no phone/control-link dependency and no persistent board firmware changes.

