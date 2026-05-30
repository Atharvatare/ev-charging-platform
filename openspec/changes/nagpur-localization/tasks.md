# Tasks Checklist: Nagpur Localization & Filters

- [x] Seeding & Schema Updates
  - [x] Add Kalmeshwar, Nagpur Flagship station to `app/core/seed.py`
  - [x] Update station count validation from 24 to 25 in `app/core/seed.py`
  - [x] Update database test assertion in `tests/test_main.py`
- [x] Registered Office Update
  - [x] Relocate Registered Office address in `app/templates/support.html` to Kalmeshwar, Nagpur
- [x] Interactive Map Sidebar Filters
  - [x] Inject Sleek Glassmorphic dropdowns for Country, State, and City in `app/templates/portal.html`
  - [x] Implement robust JS address parsing function `parseStationAddress(address)`
  - [x] Implement Alpine.js data reactive properties & dynamic unique options computation
  - [x] Implement Leaflet visibility filters `filterMarkers()` and dynamic fitting `zoomToFilteredStations()`
- [x] Verification
  - [x] Run automated pytest suite to confirm all tests pass cleanly
  - [x] Verify homepage, portal view, and support hubs load successfully
