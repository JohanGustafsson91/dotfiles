import copy
from datetime import datetime
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


loader = importlib.machinery.SourceFileLoader("vasttrafik", str(Path(__file__).resolve().parents[1] / "i3/vasttrafik"))
spec = importlib.util.spec_from_loader(loader.name, loader)
vt = importlib.util.module_from_spec(spec)
loader.exec_module(vt)

NOW = vt.parse_time("2026-10-06T15:00:00+02:00")


def setUpModule():
    directory = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(directory.cleanup)
    usage_patch = patch.object(vt, "USAGE", Path(directory.name) / "usage.jsonl")
    usage_patch.start()
    unittest.addModuleCleanup(usage_patch.stop)


class UsageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        usage_patch = patch.object(vt, "USAGE", Path(directory.name) / "state/usage.jsonl")
        usage_patch.start()
        self.addCleanup(usage_patch.stop)
        environment = patch.dict(vt.os.environ, {"VASTTRAFIK_TRACKING": "1"})
        environment.start()
        self.addCleanup(environment.stop)

    def test_private_append_and_summary_without_config_or_network(self):
        with patch.object(vt, "datetime") as clock:
            clock.now.return_value = NOW
            vt.track_usage("Meny öppnad: terminal")
            vt.track_usage("Meny öppnad: terminal")
        records = [json.loads(line) for line in vt.USAGE.read_text().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0], {"time": NOW.isoformat(), "event": "Meny öppnad: terminal"})
        self.assertEqual(vt.USAGE.stat().st_mode & 0o777, 0o600)
        self.assertEqual(vt.USAGE.parent.stat().st_mode & 0o777, 0o700)
        with vt.USAGE.open("a") as file:
            file.write('{"broken":\n')
        with patch.object(vt.sys, "argv", ["vasttrafik", "--usage"]), \
                patch.object(vt, "load_json") as config, \
                patch.object(vt.Client, "get") as request, \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            vt.main()
        config.assert_not_called()
        request.assert_not_called()
        self.assertIn("Meny öppnad: terminal: 2", output.getvalue())
        self.assertIn("2026-10-06: 2", output.getvalue())
        self.assertIn("15:00–15:59: 2", output.getvalue())
        self.assertIn("Överhoppade skadade loggrader: 1", output.getvalue())
        self.assertEqual(len(vt.USAGE.read_text().splitlines()), 3)

    def test_disabled_or_unwritable_log_does_not_break_program(self):
        with patch.dict(vt.os.environ, {"VASTTRAFIK_TRACKING": "0"}):
            vt.track_usage("test")
        self.assertFalse(vt.USAGE.exists())
        with patch.object(vt.os, "open", side_effect=OSError("disk full")):
            vt.track_usage("test")
        self.assertFalse(vt.USAGE.exists())

    def test_menu_logs_actions_but_not_typed_text_or_route_names(self):
        config = {"origin": "Private origin", "destination": "Private destination"}
        with patch.object(vt, "current_watch", return_value=None), \
                patch.object(vt, "seen_alerts", return_value=[]), \
                patch.object(vt, "rofi", side_effect=["Private typed text", "Åk så snart som möjligt", None]), \
                patch.object(vt, "load_routes", return_value=({}, None)), \
                patch.object(vt, "progress"):
            vt.show_journeys(config, {}, None)
        log = vt.USAGE.read_text()
        self.assertNotIn("Private", log)
        self.assertIn("Menyval: Åk så snart som möjligt", log)
        self.assertIn("Meny stängd", log)


def journey(departure="15:10", arrival="15:25", line="7"):
    from datetime import timedelta

    def call(clock, name):
        return {"plannedTime": f"2026-10-06T{clock}:00+02:00",
                "stopPoint": {"name": name, "platform": "A", "stopArea": {"name": name}}}

    start = vt.parse_time(f"2026-10-06T{departure}:00+02:00")
    tram_arrival = (start + timedelta(minutes=5)).strftime("%H:%M")
    train_departure = (start + timedelta(minutes=10)).strftime("%H:%M")
    return {"tripLegs": [{
        "origin": call(departure, "Kaptensgatan"),
        "destination": call(tram_arrival, "Drottningtorget"),
        "isCancelled": False,
        "serviceJourney": {"line": {"shortName": line, "transportMode": "tram"}, "direction": "Bergsjön"},
        "journeyLegIndex": 0,
    }, {
        "origin": call(train_departure, "Göteborg Central"),
        "destination": call(arrival, "Trollhättan resecentrum"),
        "serviceJourney": {"line": {"shortName": "V-TÅG", "transportMode": "train"}},
        "journeyLegIndex": 2,
    }], "connectionLinks": [{"journeyLegIndex": 1, "plannedDurationInMinutes": 3}]}


class JourneyTests(unittest.TestCase):
    def test_every_departure_shows_place_and_current_platform(self):
        result = journey()
        result["tripLegs"][-1]["origin"]["estimatedPlatform"] = "7"
        option = vt.journey_options([result], NOW)[0]
        self.assertIn("från Kaptensgatan, läge A", option["label"])
        self.assertIn("från Göteborg Central, spår 7", option["label"])
        self.assertTrue(any("från Göteborg Central, spår 7" in row for row in vt.watched_times(result, {})))
        tram = result["tripLegs"][0]
        tram["origin"]["realtimeStopPoint"] = {"name": "Annan hållplats"}
        self.assertEqual(vt.departure_place(tram), "Annan hållplats, läge ej angivet")

    def test_watch_times_distinguish_forecasts_timetable_and_cancellations(self):
        result = journey()
        result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:12:00+02:00"
        result["tripLegs"][-1]["destination"]["estimatedTime"] = "2026-10-06T15:27:00+02:00"
        rows = vt.watched_times(result, {})
        self.assertIn("beräknad 15:12 (+2 min; tidtabell 15:10)", rows[0])
        self.assertIn("tidtabell 15:15 (prognos saknas)", rows[1])
        self.assertIn("hemma: cirka 15:37 (senaste prognos + 10 min", rows[-1])
        result["tripLegs"][-1]["isCancelled"] = True
        rows = vt.watched_times(result, {})
        self.assertTrue(any("inställd" in row for row in rows))
        self.assertFalse(any("hemma:" in row for row in rows))

    def test_delayed_tram_cannot_use_stale_walk_arrival(self):
        result = journey()
        train = result["tripLegs"][-1]
        train["origin"]["plannedTime"] = "2026-10-06T15:23:00+02:00"
        feeder = {"tripLegs": result["tripLegs"][:1], "arrivalAccessLink": {
            "plannedArrivalTime": "2026-10-06T15:18:00+02:00", "plannedDurationInMinutes": 3}}
        self.assertIsNotNone(vt.connect_train(feeder, train, NOW))
        feeder["tripLegs"][0]["destination"]["estimatedTime"] = "2026-10-06T15:19:00+02:00"
        self.assertIsNone(vt.connect_train(feeder, train, NOW))
        feeder["arrivalAccessLink"]["estimatedArrivalTime"] = "2026-10-06T15:18:00+02:00"
        self.assertIsNone(vt.connect_train(feeder, train, NOW))

    def test_cancelled_departures_warn_without_becoming_recommendations(self):
        for field in ("isCancelled", "isPartCancelled"):
            result = journey()
            result["tripLegs"][-1][field] = True
            self.assertEqual(vt.journey_options([result], NOW), [])
            self.assertEqual(len(vt.traffic_alerts([result, result], NOW, "C")), 1)
            self.assertEqual(vt.traffic_alerts([result], NOW, "G"), [])
            self.assertEqual(vt.traffic_alerts([result], vt.parse_time("2026-10-06T16:00:00+02:00")), [])

    def test_same_train_keeps_both_stations_central_first(self):
        central = journey("15:10", "16:38")
        central["tripLegs"][-1]["serviceJourney"]["gid"] = "same-train"
        gamlestaden = copy.deepcopy(central)
        gamlestaden["tripLegs"][-1]["origin"]["stopPoint"]["stopArea"]["name"] = "Gamlestaden Station"
        options = vt.journey_options([gamlestaden, central, central], NOW)
        selected = vt.arrival_alternatives(options, vt.arrival_deadline("17", NOW))
        self.assertEqual([option["via"] for option in selected], ["C", "G"])

    def test_stitched_connection_keeps_walk_and_requires_five_minutes(self):
        original = journey()
        train = original["tripLegs"][-1]
        train["origin"]["stopPoint"]["gid"] = "train-platform"
        train["origin"]["plannedTime"] = "2026-10-06T15:23:00+02:00"
        feeder = {"tripLegs": original["tripLegs"][:1], "arrivalAccessLink": {
            "plannedArrivalTime": "2026-10-06T15:18:00+02:00",
            "plannedDurationInMinutes": 3,
        }, "detailsReference": "feeder-only"}
        before = copy.deepcopy(feeder)
        connected = vt.connect_train(feeder, train, NOW)
        self.assertEqual(feeder, before)
        self.assertNotIn("detailsReference", connected)
        self.assertNotIn("arrivalAccessLink", connected)
        self.assertEqual(connected["connectionLinks"][0]["destination"]["stopPoint"]["gid"], "train-platform")
        self.assertEqual(vt.journey_options([connected], NOW)[0]["margin"], 5)
        feeder["arrivalAccessLink"]["estimatedArrivalTime"] = "2026-10-06T15:19:00+02:00"
        self.assertIsNone(vt.connect_train(feeder, train, NOW))

    def test_stitch_rejects_missing_walk_and_cancelled_tram(self):
        original = journey()
        train = original["tripLegs"][-1]
        train["origin"]["stopPoint"]["gid"] = "train-platform"
        feeder = {"tripLegs": original["tripLegs"][:1]}
        self.assertIsNone(vt.connect_train(feeder, train, NOW))
        feeder["tripLegs"][0]["destination"]["stopPoint"]["gid"] = "train-platform"
        self.assertIsNotNone(vt.connect_train(feeder, train, NOW))
        feeder["tripLegs"][0]["isCancelled"] = True
        self.assertIsNone(vt.connect_train(feeder, train, NOW))

    def test_four_arrivals_before_target_and_one_after(self):
        deadline = vt.arrival_deadline("17", NOW)
        self.assertEqual(deadline.strftime("%H:%M"), "17:00")
        results = [journey("15:10", arrival) for arrival in
                   ["15:30", "16:00", "16:15", "16:40", "17:00", "17:10", "17:25"]]
        options = vt.journey_options(results, NOW, deadline, include_later=True)
        selected = vt.arrival_alternatives(options, deadline)
        self.assertEqual([option["arrival"].strftime("%H:%M") for option in selected],
                         ["17:00", "16:40", "16:15", "16:00", "17:10"])

    def test_arrival_alternatives_are_two_distinct_trains_closest_to_deadline(self):
        results = [
            journey("15:30", "16:00"),
            journey("15:10", "16:43"),
            journey("15:20", "16:38"),
            journey("15:15", "16:43"),
            journey("15:40", "16:46"),
        ]
        options = vt.journey_options(results, NOW, vt.arrival_deadline("16:45", NOW))
        selected = vt.arrival_alternatives(options)
        self.assertEqual([option["arrival"].strftime("%H:%M") for option in selected], ["16:43", "16:38"])
        self.assertEqual(selected[0]["departure"].strftime("%H:%M"), "15:15")

    def test_next_and_latest_feasible_departure(self):
        results = [journey("15:20", "15:35"), journey(), journey("15:15", "15:29")]
        next_options = vt.journey_options(results, NOW)
        options = vt.journey_options(results, NOW, vt.arrival_deadline("15:30", NOW))
        self.assertEqual(next_options[0]["departure"].strftime("%H:%M"), "15:10")
        self.assertEqual(options[0]["departure"].strftime("%H:%M"), "15:15")
        self.assertEqual(len(options), 2)

    def test_realtime_delay_disqualifies_deadline(self):
        result = journey()
        result["tripLegs"][-1]["destination"]["estimatedTime"] = "2026-10-06T15:40:00+02:00"
        self.assertEqual(vt.journey_options([result], NOW, vt.arrival_deadline("15:30", NOW)), [])

    def test_departed_cancelled_partial_and_non_trams_are_excluded(self):
        results = [journey() for _ in range(4)]
        results[0]["isDeparted"] = True
        results[1]["tripLegs"][0]["isCancelled"] = True
        results[2]["tripLegs"][0]["isPartCancelled"] = True
        results[3]["tripLegs"][0]["serviceJourney"]["line"]["transportMode"] = "bus"
        self.assertEqual(vt.journey_options(results + [journey("14:59")], NOW, via="C"), [])

    def test_return_trip_accepts_train_then_tram(self):
        result = journey()
        first, second = result["tripLegs"]
        first["serviceJourney"]["line"] = {"transportMode": "train", "shortName": "V-TÅG"}
        first["origin"]["stopPoint"]["name"] = "Trollhättan resecentrum"
        first["destination"]["stopPoint"]["stopArea"]["name"] = "Göteborg Central"
        second["serviceJourney"]["line"] = {"transportMode": "tram", "shortName": "11"}
        second["destination"]["stopPoint"]["name"] = "Kaptensgatan"
        option = vt.journey_options([result], NOW, via="C")[0]
        self.assertIn("V-TÅG 15:10 från Trollhättan resecentrum, spår A", option["label"])
        self.assertIn("11 15:20 från Göteborg Central, läge A", option["label"])
        self.assertEqual(option["margin"], 2)

    def test_custom_route_allows_direct_bus(self):
        result = journey()
        result["tripLegs"] = result["tripLegs"][:1]
        result["connectionLinks"] = []
        result["tripLegs"][0]["serviceJourney"]["line"]["transportMode"] = "bus"
        option = vt.journey_options([result], NOW, via="all")[0]
        self.assertIsNone(option["margin"])
        self.assertEqual(len(vt.arrival_alternatives([option])), 1)

    def test_changed_platform_and_walking_margin(self):
        result = journey()
        result["tripLegs"][0]["origin"]["realtimeStopPoint"] = {"name": "Kaptensgatan", "platform": "B"}
        option = vt.journey_options([result], NOW)[0]
        self.assertIn("7 15:10 från Kaptensgatan, läge B", option["label"])
        self.assertIn("~15:25", option["label"])
        self.assertEqual(option["margin"], 2)
        self.assertFalse(option["warning"])

    def test_insufficient_walking_time_is_excluded(self):
        result = journey()
        result["connectionLinks"][0]["plannedDurationInMinutes"] = 6
        self.assertEqual(vt.journey_options([result], NOW), [])

    def test_station_filter_and_call_disruption(self):
        result = journey()
        note = {"text": "Banarbete – tåg inställt senare ikväll", "type": "disruption-message"}
        result["tripLegs"][-1]["origin"]["notes"] = [note]
        result["tripLegs"][-1]["notes"] = [note]
        self.assertEqual(vt.journey_options([result], NOW, via="G"), [])
        option = vt.journey_options([result], NOW, via="C")[0]
        self.assertFalse(option["warning"])
        self.assertNotIn(note["text"], option["details"])

    def test_invalid_or_past_deadline_is_rejected(self):
        for value in ["24:00", "15:60", "tomorrow", "15:00", "14:00"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                vt.arrival_deadline(value, NOW)


class ClientTests(unittest.TestCase):
    def test_earlier_direct_tram_preferred_over_later_extra_change(self):
        train = journey("15:40", "16:40")["tripLegs"][-1]
        train["serviceJourney"]["gid"] = "same-train"
        train["origin"]["stopPoint"]["gid"] = "platform"
        direct = {"tripLegs": journey("15:10", line="11")["tripLegs"][:1],
                  "arrivalAccessLink": {"plannedArrivalTime": "2026-10-06T15:18:00+02:00",
                                        "plannedDurationInMinutes": 3}}
        indirect = {"tripLegs": [journey("15:20", line="3")["tripLegs"][0],
                                journey("15:30", line="1")["tripLegs"][0]],
                    "arrivalAccessLink": {"plannedArrivalTime": "2026-10-06T15:38:00+02:00",
                                          "plannedDurationInMinutes": 3}}
        indirect["tripLegs"][1]["journeyLegIndex"] = 1
        for previous_results, expected_line in [([direct], "11"), ([], "3")]:
            with self.subTest(previous_results=bool(previous_results)):
                client = vt.Client({}, {})
                pages = [{"results": [{"tripLegs": [train]}]},
                         {"results": [indirect], "links": {"previous": "?paginationReference=earlier"}},
                         {"results": previous_results}]
                with patch.object(client, "stop", return_value="station"), \
                        patch.object(client, "get", side_effect=pages) as request:
                    results = client.journeys(vt.arrival_deadline("17", NOW), NOW, ["C"])
                selected = vt.best_connections(vt.journey_options(results, NOW, via="C"))
                self.assertEqual(len(selected), 1)
                self.assertTrue(selected[0]["label"].startswith(expected_line + " "))
                self.assertEqual(request.call_count, 3)

    def test_next_search_stops_after_one_feasible_train_and_ignores_later_alerts(self):
        first = journey("15:20", "16:20")["tripLegs"][-1]
        first["origin"]["stopPoint"]["gid"] = "platform"
        first["serviceJourney"]["gid"] = "first"
        later = journey("18:10", "18:50")["tripLegs"][-1]
        later["isCancelled"] = True
        feeder = {"tripLegs": journey()["tripLegs"][:1], "arrivalAccessLink": {
            "plannedArrivalTime": "2026-10-06T15:18:00+02:00", "plannedDurationInMinutes": 3}}
        def response(path, params):
            return {"results": [{"tripLegs": [first]}, {"tripLegs": [later]}]
                    if params["transportModes"] == "train" else [feeder]}
        with patch.object(self.client, "stop", return_value="station"), \
                patch.object(self.client, "get", side_effect=response) as request:
            results = self.client.journeys(None, NOW, ["C"])
        self.assertEqual(request.call_count, 2)
        self.assertEqual(len(vt.journey_options(results, NOW, via="C")), 1)
        self.assertEqual(vt.traffic_alerts(results, NOW), [])

    def test_failed_connection_tries_earlier_train_from_previous_page(self):
        trains = []
        for identity, arrival in [("closest", "16:50"), ("earlier", "16:30")]:
            train = journey("15:20", arrival)["tripLegs"][-1]
            train["serviceJourney"]["gid"] = identity
            train["origin"]["stopPoint"]["gid"] = identity
            trains.append({"tripLegs": [train]})
        feeder = {"tripLegs": journey()["tripLegs"][:1], "arrivalAccessLink": {
            "plannedArrivalTime": "2026-10-06T15:18:00+02:00", "plannedDurationInMinutes": 3}}
        def response(path, params):
            if params["transportModes"] == "train":
                if params.get("paginationReference"):
                    return {"results": trains[1:]}
                return {"results": trains[:1], "links": {"previous": "?paginationReference=previous"}}
            return {"results": [feeder] if params["destinationGid"] == "earlier" else []}
        with patch.object(self.client, "stop", return_value="station"), \
                patch.object(self.client, "get", side_effect=response) as request:
            results = self.client.journeys(vt.arrival_deadline("17", NOW), NOW, ["C"])
        self.assertEqual(request.call_count, 4)
        self.assertEqual(vt.journey_options(results, NOW)[0]["train_id"], ("earlier",))

    def test_failed_feeders_have_bounded_request_budget(self):
        trains = []
        for index in range(10):
            train = journey("15:20", "16:30")["tripLegs"][-1]
            train["origin"]["stopPoint"]["gid"] = str(index)
            train["serviceJourney"]["gid"] = str(index)
            trains.append({"tripLegs": [train]})
        def response(path, params):
            if params["transportModes"] == "train":
                return {"results": trains}
            return {"results": [], "links": {"previous": "?paginationReference=previous"}}
        with patch.object(self.client, "stop", return_value="station"), \
                patch.object(self.client, "get", side_effect=response) as request:
            self.assertEqual(self.client.journeys(None, NOW, ["C"]), [])
        self.assertEqual(request.call_count, 7)

    def test_cancelled_train_is_retained_without_extra_requests(self):
        train = journey()["tripLegs"][-1]
        train["isCancelled"] = True
        with patch.object(self.client, "stop", return_value="station"), \
                patch.object(self.client, "get", return_value={"results": [{"tripLegs": [train]}]}) as request:
            results = self.client.journeys(None, NOW, ["C"])
        request.assert_called_once()
        self.assertEqual(vt.journey_options(results, NOW, via="C"), [])
        self.assertEqual(len(vt.traffic_alerts(results, NOW, "C")), 1)
        routes = {"C": {"results": results, "fetched": NOW.timestamp()}}
        self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋 !")

    def test_station_searches_overlap_and_preserve_both_cached_responses(self):
        barrier = Barrier(2)

        def response(path, params):
            barrier.wait(timeout=2)
            return {"results": [params["station"]]}

        def station_search(deadline, now, stations):
            return self.client.cached_query({"station": stations[0]})["results"]

        with patch.object(self.client, "get", side_effect=response) as request, \
                patch.object(self.client, "station_connections", side_effect=station_search):
            self.assertEqual(self.client.train_connections(None, NOW), ["C", "G"])
            self.assertEqual(request.call_count, 2)
            self.assertEqual(self.client.train_connections(None, NOW), ["C", "G"])
            self.assertEqual(request.call_count, 2)
        self.assertEqual(len(self.client.state["connection_queries"]), 2)

    def test_parallel_station_error_reaches_existing_backoff(self):
        def station_search(deadline, now, stations):
            if stations == ["C"]:
                raise HTTPError("test", 429, "rate limit", {"Retry-After": "120"}, None)
            return []

        with patch.object(self.client, "station_connections", side_effect=station_search):
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
        self.assertEqual(self.client.state["error"], "HTTP 429")
        self.assertEqual(self.client.state["retry_at"], NOW.timestamp() + 120)

    def test_expanding_train_search_only_fetches_new_feeder(self):
        trains = []
        for index, arrival in enumerate(["16:30", "16:50", "17:10"]):
            train = journey(f"15:{10 + index * 10}", arrival)["tripLegs"][-1]
            train["origin"]["stopPoint"]["gid"] = "platform"
            train["serviceJourney"]["gid"] = str(index)
            trains.append({"tripLegs": [train]})
        feeder = {"tripLegs": journey()["tripLegs"][:1], "arrivalAccessLink": {
            "plannedArrivalTime": "2026-10-06T15:15:00+02:00", "plannedDurationInMinutes": 0}}

        def response(path, params):
            return {"results": trains if params["transportModes"] == "train" else [feeder]}

        with patch.object(self.client, "stop", return_value="station"), \
                patch.object(self.client, "get", side_effect=response) as request:
            first = self.client.journeys(vt.arrival_deadline("17", NOW), NOW, ["C"])
            self.assertEqual(len(first), 1)
            self.assertEqual(first[0]["tripLegs"][-1]["serviceJourney"]["gid"], "1")
            self.assertEqual(request.call_count, 2)
            self.client.config["_arrival_before"] = 2
            self.assertEqual(len(self.client.journeys(vt.arrival_deadline("17", NOW), NOW, ["C"])), 2)
            self.assertEqual(request.call_count, 3)
            self.client.config["_arrival_after"] = 1
            self.assertEqual(len(self.client.journeys(vt.arrival_deadline("17", NOW), NOW, ["C"])), 3)
            self.assertEqual(request.call_count, 4)

    def test_single_station_skips_other_station_requests(self):
        with patch.object(self.client, "stop", side_effect=lambda name: name), \
                patch.object(self.client, "cached_query", return_value={"results": []}) as request:
            self.client.journeys(None, NOW, ["C"])
        request.assert_called_once()
        self.assertEqual(request.call_args.args[0]["originGid"], "Göteborg Central")

    def test_station_selection_has_separate_result_cache(self):
        with patch.object(self.client, "journeys", return_value=[]) as request:
            vt.fetch_routes(self.client, ["C"], None, NOW)
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args[2], ["C", "G"])

    def test_read_only_cache_never_fetches_even_when_empty_or_expired(self):
        with patch.object(self.client, "journeys", return_value=[journey()]) as request:
            empty = vt.fetch_routes(self.client, ["C", "G"], None, NOW, refresh=False)
            request.assert_not_called()
            self.assertEqual(empty["C"], {})
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
            request.reset_mock()
            with patch.object(vt.time, "time", return_value=NOW.timestamp() + 3600):
                cached = vt.fetch_routes(self.client, ["C", "G"], None, NOW, refresh=False)
            request.assert_not_called()
            self.assertEqual(len(cached["C"]["results"]), 1)

    def test_connection_queries_share_cache_and_expire(self):
        with patch.object(self.client, "get", return_value={"results": []}) as request:
            self.client.cached_query({"originGid": "C"})
            self.client.cached_query({"originGid": "C"})
            self.assertEqual(request.call_count, 1)
            with patch.object(vt.time, "time", return_value=NOW.timestamp() + 61):
                self.client.cached_query({"originGid": "C"})
            self.assertEqual(request.call_count, 2)

    def test_arrival_pagination_can_search_both_sides(self):
        client = vt.Client({"origin": "A", "destination": "B", "_arrival_before": 4, "_arrival_after": 1}, {})
        pages = [
            {"results": [journey("15:10", "16:55")], "links": {
                "previous": "?paginationReference=earlier", "next": "?paginationReference=later"}},
            {"results": [journey("15:10", "17:05")]},
            {"results": [journey("15:10", value) for value in ["16:45", "16:35", "16:25"]]},
        ]
        with patch.object(client, "stop", return_value="test"), \
                patch.object(client, "get", side_effect=pages) as request:
            results = client.journeys(vt.arrival_deadline("17", NOW), NOW)
        self.assertEqual(request.call_count, 3)
        self.assertEqual(len(results), 5)

    def setUp(self):
        self.clock = patch.object(vt.time, "time", return_value=NOW.timestamp())
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.client = vt.Client({"client_id": "test-id", "client_secret": "test-secret"}, {})

    def test_token_reused_and_rotated_credentials_invalidate_it(self):
        responses = [{"access_token": "test-token", "expires_in": 3600}, {}, {},
                     {"access_token": "new-token", "expires_in": 3600}, {}]
        with patch.object(self.client, "request", side_effect=responses) as request:
            self.client.get("journeys", {})
            self.client.get("journeys", {})
            self.client.config["client_secret"] = "changed"
            self.client.get("journeys", {})
        token_calls = [call for call in request.call_args_list if call.args[0] == vt.TOKEN_URL]
        self.assertEqual(len(token_calls), 2)

    def test_arrival_search_fetches_earlier_centralen_alternative(self):
        self.client.config.update(origin="A", destination="B")
        gamlestaden = journey()
        gamlestaden["tripLegs"][-1]["origin"]["stopPoint"]["stopArea"]["name"] = "Gamlestaden Station"
        pages = [
            {"results": [gamlestaden, journey("15:20", "15:40")],
             "links": {"previous": "https://ext-api.vasttrafik.se/pr/v4/journeys?paginationReference=earlier"}},
            {"results": [journey()]},
        ]
        deadline = vt.arrival_deadline("15:30", NOW)
        with patch.object(self.client, "stop", return_value="test-gid"), \
                patch.object(self.client, "get", side_effect=pages) as request:
            results = self.client.journeys(deadline, NOW, ["C", "G"])
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args[1]["paginationReference"], "earlier")
        self.assertEqual(len(vt.journey_options(results, NOW, deadline, "C")), 1)

    def test_two_destinations_share_cache_across_clients(self):
        with patch.object(self.client, "journeys", return_value=[journey()]) as fetch:
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
            self.assertEqual(fetch.call_count, 1)
        other = vt.Client(self.client.config, copy.deepcopy(self.client.state))
        with patch.object(other, "journeys") as fetch:
            vt.fetch_routes(other, ["C", "G"], None, NOW)
            fetch.assert_not_called()

    def test_reverse_route_does_not_reuse_outbound_cache(self):
        with patch.object(self.client, "journeys", return_value=[journey()]):
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
        self.client.config.update(origin="Trollhättan resecentrum", destination="Kaptensgatan")
        with patch.object(self.client, "journeys", return_value=[]) as fetch:
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
        fetch.assert_called_once()

    def test_custom_endpoints_are_sent_to_api(self):
        self.client.config.update(origin="A", origin_gid="123", destination="B", destination_gid="456")
        with patch.object(self.client, "get", return_value={"results": []}) as request:
            self.client.journeys(None, NOW)
        params = request.call_args.args[1]
        self.assertEqual(params["originGid"], "123")
        self.assertEqual(params["destinationGid"], "456")
        self.assertNotIn("transportModes", params)

    def test_rate_limit_applies_to_other_destinations_and_searches(self):
        error = HTTPError(vt.API, 429, "limited", {"Retry-After": "600"}, None)
        with patch.object(self.client, "journeys", side_effect=error) as fetch:
            vt.fetch_routes(self.client, ["C", "G"], None, NOW)
            vt.fetch_routes(self.client, ["G"], vt.arrival_deadline("16:00", NOW), NOW)
            self.assertEqual(fetch.call_count, 1)
        self.assertEqual(self.client.state["retry_at"], NOW.timestamp() + 600)

    def test_network_error_retains_marked_cache(self):
        with patch.object(self.client, "journeys", return_value=[journey()]):
            vt.fetch_routes(self.client, ["C"], None, NOW)
        with patch.object(vt.time, "time", return_value=NOW.timestamp() + 61):
            with patch.object(self.client, "journeys", side_effect=URLError("offline")):
                routes = vt.fetch_routes(self.client, ["C"], None, NOW)
            text, color = vt.render(routes, None, NOW, self.client.state["error"], 60)
        self.assertEqual(text, "🚋 ?")
        self.assertEqual(color, "warning")

    def test_retry_after_http_date(self):
        self.assertEqual(vt.retry_delay("Tue, 06 Oct 2026 13:10:00 GMT", NOW.timestamp()), 600)
        self.assertEqual(vt.retry_delay(None, NOW.timestamp()), 300)

    def test_ambiguous_stop_is_not_silently_chosen(self):
        with patch.object(self.client, "get", return_value={"results": [
            {"name": "Kaptensgatan, Göteborg", "gid": "1"},
            {"name": "Kaptensgatan, Göteborg", "gid": "2"},
        ]}):
            with self.assertRaises(ValueError):
                self.client.stop("Kaptensgatan")


class PauseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        config_patch = patch.object(vt, "CONFIG", Path(directory.name) / "config.json")
        config_patch.start()
        self.addCleanup(config_patch.stop)
        cache_patch = patch.object(vt, "CACHE", Path(directory.name))
        cache_patch.start()
        self.addCleanup(cache_patch.stop)

    def test_pause_expires_next_day_and_blocks_reminder(self):
        vt.pause_today(NOW)
        self.assertTrue(vt.paused_today(NOW))
        self.assertFalse(vt.paused_today(NOW.replace(day=7)))
        with patch.object(vt, "current_watch") as watch, patch.object(vt.subprocess, "run") as notify:
            self.assertFalse(vt.remind_to_pack(NOW))
        watch.assert_not_called()
        notify.assert_not_called()

    def test_paused_panel_does_not_fetch_or_send_reminders(self):
        vt.pause_today(NOW)
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.sys, "argv", ["vasttrafik"]), \
                patch.dict(vt.os.environ, {"BLOCK_BUTTON": ""}), \
                patch.object(vt, "load_routes") as fetch, \
                patch.object(vt, "remind_to_pack") as remind, \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            clock.now.return_value = NOW
            vt.main()
        fetch.assert_not_called()
        remind.assert_not_called()
        self.assertIn("🚋 ⏸", output.getvalue())

    def test_paused_menu_can_resume(self):
        vt.pause_today(NOW)
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.sys, "argv", ["vasttrafik", "--menu"]), \
                patch.object(vt, "rofi", side_effect=["Återuppta", None]) as menu, \
                patch.object(vt, "current_watch", return_value=None), \
                patch("sys.stdout", new_callable=io.StringIO):
            clock.now.return_value = NOW
            vt.main()
        self.assertFalse(vt.paused_today(NOW))
        self.assertIn("Återuppta", menu.call_args_list[0].args[1])


class MenuTests(unittest.TestCase):
    def test_panel_warning_is_first_and_shows_watched_trip_not_search_results(self):
        watched = journey()
        watched["_watch"] = True
        watched["tripLegs"][-1]["isCancelled"] = True
        watch = {"config": {}, "via": "C", "journey": watched, "id": "watch"}
        cached = {"C": {"results": [watched], "fetched": NOW.timestamp()}}
        searches = {"C": {"results": [journey()], "fetched": NOW.timestamp()}}
        warning_choice = "! Visa varningen – bevakad resa"
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "current_watch", return_value=watch), \
                patch.object(vt, "load_routes", return_value=(cached, None)) as fetch, \
                patch.object(vt, "rofi", side_effect=[warning_choice, None, None]) as menu:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            self.assertEqual(vt.render(cached, None, NOW, None, 60, {"_watch": watch})[0], "🚋 !")
            vt.show_journeys({}, searches, None)
            self.assertEqual(vt.render(cached, None, NOW, None, 60, {"_watch": watch})[0], "🚋")
        self.assertEqual(menu.call_args_list[0].args[1][0], warning_choice)
        self.assertIn("bevakad resa", menu.call_args_list[1].args[0])
        self.assertIn("Inställd", menu.call_args_list[1].args[1][0])
        self.assertNotIn(warning_choice, menu.call_args_list[2].args[1])
        self.assertTrue(all(call.kwargs.get("refresh") is False for call in fetch.call_args_list))

    def test_closing_menu_does_not_acknowledge_panel_warning(self):
        result = journey()
        result["tripLegs"][-1]["isCancelled"] = True
        routes = {"C": {"results": [result], "fetched": NOW.timestamp()}}
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "current_watch", return_value=None), \
                patch.object(vt, "rofi", return_value=None) as menu:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            vt.show_journeys({}, routes, None)
        self.assertEqual(menu.call_args.args[1][0], "! Visa varningen – sökresultaten")
        self.assertEqual(vt.seen_alerts(NOW), set())

    def test_refresh_journeys_also_refreshes_exact_watch(self):
        watch = {"config": {"origin": "Annan start"}, "via": "all", "journey": journey(), "id": "watch"}
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt, "current_watch", return_value=watch), \
                patch.object(vt, "progress"), \
                patch.object(vt, "load_routes", return_value=({}, None)) as fetch, \
                patch.object(vt, "rofi", side_effect=["Uppdatera resorna", None]):
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            vt.show_journeys({}, {}, None)
        requests = [call for call in fetch.call_args_list if call.kwargs.get("refresh") is not False]
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].args[0]["_watch"], watch)
        self.assertEqual(requests[0].args[1], ["all"])
        self.assertTrue(requests[0].kwargs["manual"])
        self.assertNotIn("_watch", requests[1].args[0])

    def test_refresh_watched_trip_opens_its_updated_details(self):
        result = journey()
        result["_watch"] = True
        result["tripLegs"][-1]["isCancelled"] = True
        watch = {"config": {}, "via": "C", "journey": result, "id": "watch"}
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "current_watch", return_value=watch), \
                patch.object(vt, "progress"), \
                patch.object(vt, "load_routes", return_value=({"C": {"results": [result], "fetched": NOW.timestamp()}}, None)) as fetch, \
                patch.object(vt, "rofi", side_effect=["Uppdatera bevakad resa", None, None]) as menu:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            vt.show_journeys({}, {}, None)
        self.assertTrue(any(call.kwargs.get("manual") for call in fetch.call_args_list))
        self.assertIn("Bevakad resa", menu.call_args_list[1].args[0])
        self.assertTrue(any("Inställd" in row for row in menu.call_args_list[1].args[1]))

    def test_home_from_selects_only_origin_and_keeps_home_time(self):
        config = {"origin": "Trollhättan resecentrum", "origin_gid": "old-origin",
                  "destination": "Kaptensgatan", "destination_gid": "old-destination",
                  "arrival_targets": {"trollhättan resecentrum": {"label": "hemma", "minutes": 12}}}
        with patch.object(vt, "choose_stop", return_value={"name": "Göteborg Central, Göteborg", "gid": "central"}) as choose, \
                patch.object(vt, "save_route") as save:
            updated = vt.home_from(config)
        choose.assert_called_once()
        save.assert_not_called()
        self.assertEqual(updated["origin_gid"], "central")
        self.assertEqual(updated["destination"], "Trollhättan resecentrum")
        self.assertNotIn("destination_gid", updated)
        self.assertEqual(vt.arrival_target(updated), ("hemma", 12))
        self.assertEqual(vt.route_filters(updated), ["all"])
        self.assertEqual(config["destination"], "Kaptensgatan")
        with patch.object(vt, "choose_stop", return_value=None):
            self.assertIsNone(vt.home_from(config))

    def test_read_alert_hides_bar_warning_until_status_changes(self):
        result = journey()
        result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:13:00+02:00"
        routes = {"C": {"results": [result], "fetched": NOW.timestamp()}}
        with patch.object(vt.time, "time", return_value=NOW.timestamp()):
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋 !")
            alerts = vt.traffic_alerts([result], NOW)
            vt.acknowledge_alerts(alerts, NOW)
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋")
            self.assertEqual(vt.traffic_alerts([result], NOW), alerts)
            result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:14:00+02:00"
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋 !")
            vt.acknowledge_alerts(vt.traffic_alerts([result], NOW), NOW)
            result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:13:00+02:00"
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋 !")
            self.assertEqual(vt.render(routes, None, NOW, "network error", 60)[0], "🚋 ?")
        self.assertEqual(vt.seen_alerts(NOW.replace(day=7)), set())

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        cache = patch.object(vt, "CACHE", Path(directory.name))
        cache.start()
        self.addCleanup(cache.stop)

    def test_watched_view_shows_planned_leave_even_when_delayed(self):
        result = journey()
        result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:20:00+02:00"
        config = {"departure_targets": {"kaptensgatan": {"label": "kontoret", "minutes": 5}}}
        watch = {"config": config, "via": "C", "journey": result, "label": "test", "id": "watch"}
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt, "current_watch", return_value=watch), \
                patch.object(vt, "load_routes", return_value=({"C": {}}, None)) as fetch, \
                patch.object(vt, "rofi", side_effect=["Visa bevakad resa", None, None]) as menu:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            vt.show_journeys(config, {}, None)
        self.assertEqual(menu.call_args_list[1].args[1][0], "Lämna kontoret senast 15:05 (planerad avgång)")
        self.assertFalse(fetch.call_args.kwargs["refresh"])

    def test_bar_warning_waits_but_menu_alert_remains_available(self):
        result = journey("16:10", "16:50")
        result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T16:12:00+02:00"
        with patch.object(vt.time, "time", return_value=NOW.timestamp()):
            routes = {"C": {"results": [result], "fetched": NOW.timestamp()}}
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋")
            self.assertTrue(vt.traffic_alerts([result], NOW, "C"))
            config = {"departure_targets": {"kaptensgatan": {"label": "kontoret", "minutes": 5}}}
            self.assertEqual(vt.render(routes, None, NOW.replace(minute=34, second=59), None, 60, config)[0], "🚋")
            self.assertEqual(vt.render(routes, None, NOW.replace(minute=35), None, 60, config)[0], "🚋 !")

    def test_target_time_is_subtracted_and_too_near_time_rejected(self):
        with patch.object(vt, "rofi", side_effect=["Båda", "17"]):
            plan = vt.choose_plan(NOW, {})
        self.assertEqual(vt.parse_time(plan["deadline"]).strftime("%H:%M"), "16:50")
        with patch.object(vt, "rofi", side_effect=["Båda", "15:05", None]):
            self.assertIsNone(vt.choose_plan(NOW, {}))

    def test_last_leg_settings_follow_destination_when_reversing(self):
        config = {"arrival_targets": {"kaptensgatan": {"label": "kontoret", "minutes": 4}}}
        self.assertEqual(vt.arrival_target(config), ("hemma", 10))
        with patch.object(vt, "save_route"):
            reverse = vt.reverse_route(config)
            self.assertEqual(vt.arrival_target(reverse), ("kontoret", 4))
            self.assertEqual(vt.arrival_target(vt.reverse_route(reverse)), ("hemma", 10))
        self.assertEqual(vt.arrival_target({"destination": "Annan hållplats"}), ("Annan hållplats", 0))

    def test_target_settings_saved_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(vt, "CONFIG", Path(directory) / "config.json"), \
                patch.object(vt, "rofi", side_effect=["12", "hemma"]):
            updated = vt.change_arrival_target({"client_secret": "private"})
            saved = json.loads((Path(directory) / "route.json").read_text())
        self.assertEqual(vt.arrival_target(updated), ("hemma", 12))
        self.assertEqual(saved, {"arrival_targets": updated["arrival_targets"]})

    def test_alert_details_do_not_fetch(self):
        result = journey()
        result["tripLegs"][-1]["isCancelled"] = True
        routes = {"C": {"results": [result], "fetched": NOW.timestamp()}}
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "rofi", side_effect=["Förseningar och inställda avgångar…", None, None]) as menu, \
                patch.object(vt, "load_routes") as fetch:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            vt.show_journeys({}, routes, None)
        fetch.assert_not_called()
        self.assertIn("Inställd", menu.call_args_list[1].args[1][0])

    def test_arrival_loads_one_then_expands_each_side_and_resets(self):
        routes = {"C": {"results": [journey("15:10", value) for value in
                                    ["16:00", "16:30", "16:50", "17:10"]],
                         "fetched": NOW.timestamp()}}
        selections = ["Framme senast…", "Båda", "17", "Ladda en tidigare",
                      "Ladda en senare", "Framme senast…", "Båda", "17", None]
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "rofi", side_effect=selections) as menu, \
                patch.object(vt, "load_routes", return_value=(routes, None)) as fetch:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            vt.show_journeys({}, {}, None)
        counts = [(call.args[0]["_arrival_before"], call.args[0]["_arrival_after"])
                  for call in fetch.call_args_list]
        self.assertEqual(counts, [(1, 0), (2, 0), (2, 1), (1, 0)])
        for index, count in [(3, 1), (4, 2), (5, 3), (8, 1)]:
            rows = [row for row in menu.call_args_list[index].args[1] if " ≈" in row]
            self.assertEqual(len(rows), count)
        self.assertTrue(any("Hemma ≈17:00" in row for row in menu.call_args_list[3].args[1]))

    def test_reverse_route_preserves_credentials_and_swaps_ids(self):
        config = {"client_id": "private", "origin": "A", "origin_gid": "123",
                  "destination": "B", "destination_gid": "456"}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(vt, "CONFIG", Path(directory) / "config.json"):
            updated = vt.reverse_route(config)
            self.assertFalse((Path(directory) / "route.json").exists())
        self.assertEqual(updated["origin_gid"], "456")
        self.assertEqual(updated["destination_gid"], "123")
        self.assertEqual(updated["client_id"], "private")
        self.assertEqual(config["origin"], "A")

    def test_cancel_destination_does_not_save_partial_route(self):
        with patch.object(vt, "choose_stop", side_effect=[{"name": "A", "gid": "123"}, None]), \
                patch.object(vt, "save_route") as save:
            self.assertIsNone(vt.change_route({}))
        save.assert_not_called()

    def test_arrival_action_opens_time_input_and_searches_then_resets(self):
        routes = {"C": {"results": [journey()], "fetched": NOW.timestamp()}}
        selections = ["Framme senast…", "Via Centralen", "16:40", "Åk så snart som möjligt", None]
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "rofi", side_effect=selections) as menu, \
                patch.object(vt, "load_routes", return_value=(routes, None)) as fetch:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            vt.show_journeys({}, routes, None)

        self.assertIn("välj bytesstation", menu.call_args_list[1].args[0])
        self.assertEqual(menu.call_args_list[0].args[1][0], "Framme senast…")
        self.assertEqual(menu.call_args_list[1].args[1][0], "Båda")
        self.assertIn("HH:MM", menu.call_args_list[2].args[0])
        self.assertIn("hemma senast 16:40", menu.call_args_list[3].args[0])
        self.assertEqual(fetch.call_args_list[0].args[1], ["C"])
        self.assertEqual(fetch.call_args_list[0].args[2], vt.arrival_deadline("16:30", NOW))
        self.assertEqual(fetch.call_args_list[1].args[1:], (["C", "G"], None))
        self.assertIn("nästa resor", menu.call_args_list[4].args[0])

    def test_icon_distinguishes_traffic_from_transfer_risk_and_network_errors(self):
        result = journey()
        routes = {"C": {"results": [result], "fetched": NOW.timestamp()}}
        with patch.object(vt.time, "time", return_value=NOW.timestamp()):
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋")
            result["tripLegs"][0]["notes"] = [{"text": "Spårarbete"}]
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋")
            result["tripLegs"][0]["origin"]["estimatedTime"] = "2026-10-06T15:12:00+02:00"
            self.assertEqual(vt.render(routes, None, NOW, None, 60)[0], "🚋 !")
            self.assertEqual(vt.render(routes, None, NOW, "HTTP 429", 60)[0], "🚋 ?")

    def test_menu_opens_with_departures_and_selected_trip_details(self):
        routes = {"C": {"results": [journey()], "fetched": NOW.timestamp()}}
        shown = []

        def select(prompt, choices):
            shown.append((prompt, choices))
            if len(shown) == 1:
                return next(choice for choice in choices if choice.startswith("1. "))
            return None

        with patch.object(vt, "datetime") as clock, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()), \
                patch.object(vt, "rofi", side_effect=select):
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.fromtimestamp.side_effect = datetime.fromtimestamp
            clock.fromtimestamp.return_value = NOW
            vt.show_journeys({}, routes, None)
        self.assertIn("nästa resor", shown[0][0])
        self.assertTrue(any("Göteborg Central" in row for row in shown[0][1]))
        self.assertIn("Framme senast…", shown[0][1])
        self.assertIn("Resa och förseningar", shown[1][0])
        self.assertIn("Kaptensgatan", shown[1][1][1])


class WatchTests(unittest.TestCase):
    def cache_watch_result(self, result, now):
        watch = vt.load_json(vt.CONFIG.with_name("watch.json"))
        vt.save_json(vt.CACHE / "state.json", {"routes": {
            f"{watch['date']}:watch:{watch['id']}": {"results": [result], "fetched": now.timestamp()}
        }})

    def test_impossible_transfer_suppresses_home_forecast(self):
        self.result["tripLegs"][0]["destination"]["estimatedTime"] = "2026-10-06T15:17:30+02:00"
        rows = vt.watched_times(self.result, {})
        self.assertIn("Anslutningen fungerar inte – sök alternativ.", rows)
        self.assertFalse(any("hemma:" in row for row in rows))
        self.assertEqual(vt.journey_options([self.result], NOW), [])

    def test_zero_estimated_walk_overrides_planned_walk(self):
        self.result["tripLegs"][0]["destination"]["estimatedTime"] = "2026-10-06T15:19:00+02:00"
        self.result["connectionLinks"][0]["estimatedDurationInMinutes"] = 0
        self.assertIsNone(vt.journey_problem(self.result))
        self.assertTrue(vt.journey_options([self.result], NOW))

    def test_reminder_uses_cached_cancellation_and_transfer_failure(self):
        for problem in ("cancelled", "transfer"):
            with self.subTest(problem=problem), patch.object(vt.subprocess, "run") as notify:
                vt.save_watch({}, vt.journey_options([self.result], NOW)[0], NOW)
                updated = copy.deepcopy(self.result)
                if problem == "cancelled":
                    updated["tripLegs"][1]["isCancelled"] = True
                else:
                    updated["tripLegs"][0]["destination"]["estimatedTime"] = "2026-10-06T15:24:00+02:00"
                due = NOW.replace(minute=8)
                self.cache_watch_result(updated, due)
                self.assertTrue(vt.remind_to_pack(due))
                self.assertIn("Välj en annan resa", notify.call_args.args[0])
                self.assertEqual(notify.call_args.args[0][-1], vt.journey_problem(updated))

    def test_reminder_marks_missing_or_old_traffic_data(self):
        vt.save_watch({}, vt.journey_options([self.result], NOW)[0], NOW)
        with patch.object(vt.subprocess, "run") as notify:
            self.assertTrue(vt.remind_to_pack(NOW.replace(minute=8)))
            self.assertIn("inte nyligen uppdaterat", notify.call_args.args[0][-1])
        vt.save_watch({}, vt.journey_options([self.result], NOW)[0], NOW)
        self.cache_watch_result(self.result, NOW)
        with patch.object(vt.subprocess, "run") as notify:
            self.assertTrue(vt.remind_to_pack(NOW.replace(minute=8)))
            self.assertIn("inte nyligen uppdaterat", notify.call_args.args[0][-1])

    def test_delayed_watch_extends_expiry_but_is_bounded_and_clearable(self):
        vt.save_watch({}, vt.journey_options([self.result], NOW)[0], NOW)
        self.result["tripLegs"][1]["destination"]["estimatedTime"] = "2026-10-06T17:25:00+02:00"
        self.cache_watch_result(self.result, NOW)
        self.assertIsNotNone(vt.current_watch(NOW.replace(hour=17)))
        self.assertIsNone(vt.current_watch(NOW.replace(hour=18, minute=5)))
        self.result["tripLegs"][1]["destination"]["estimatedTime"] = "2026-10-06T23:25:00+02:00"
        self.cache_watch_result(self.result, NOW)
        self.assertIsNotNone(vt.current_watch(NOW.replace(hour=19, minute=4)))
        self.assertIsNone(vt.current_watch(NOW.replace(hour=19, minute=5)))
        vt.clear_watch()
        self.assertIsNone(vt.current_watch(NOW.replace(hour=17)))

    def test_watch_forecast_includes_final_walk_after_delayed_train(self):
        self.result["tripLegs"][1]["destination"]["estimatedTime"] = "2026-10-06T15:30:00+02:00"
        self.result["arrivalAccessLink"] = {"plannedArrivalTime": "2026-10-06T15:29:00+02:00",
                                            "plannedDurationInMinutes": 4}
        self.assertTrue(any("15:44" in row for row in vt.watched_times(self.result, {})))

    def test_watch_preserves_updated_platform_from_details(self):
        call = self.responses[1]["tripLegs"][0]["serviceJourneys"][0]["callsOnServiceJourney"][0]
        call.update(plannedPlatform="7", estimatedPlatform="9")
        client = vt.Client({}, {})
        with patch.object(client, "get", side_effect=self.responses):
            result = client.watched_journey(self.watch)[0]
        self.assertEqual(vt.departure_place(result["tripLegs"][1]), "Göteborg Central, spår 9")

    def test_pack_reminder_once_and_never_after_leave_time(self):
        option = vt.journey_options([self.result], NOW)[0]
        vt.save_watch({}, option, NOW)
        with patch.object(vt, "CACHE", Path(self.directory.name)), \
                patch.object(vt.subprocess, "run") as notify:
            self.assertFalse(vt.remind_to_pack(NOW.replace(minute=7, second=59)))
            self.assertTrue(vt.remind_to_pack(NOW.replace(minute=8)))
            self.assertFalse(vt.remind_to_pack(NOW.replace(minute=9)))
            notify.assert_called_once()
            self.assertIn("Gå senast 15:10.", notify.call_args.args[0][-1])
            vt.save_watch({}, option, NOW)
            self.assertFalse(vt.remind_to_pack(NOW.replace(minute=10)))
            self.assertTrue(vt.remind_to_pack(NOW.replace(minute=8)))
            self.assertEqual(notify.call_count, 2)
            vt.clear_watch()
            self.assertFalse(vt.remind_to_pack(NOW.replace(minute=8)))

    def test_failed_notification_can_retry_without_marking_sent(self):
        option = vt.journey_options([self.result], NOW)[0]
        vt.save_watch({}, option, NOW)
        with patch.object(vt, "CACHE", Path(self.directory.name)), \
                patch.object(vt.subprocess, "run", side_effect=[OSError("desktop unavailable"), None]) as notify:
            self.assertFalse(vt.remind_to_pack(NOW.replace(minute=8)))
            self.assertTrue(vt.remind_to_pack(NOW.replace(minute=9)))
            self.assertEqual(notify.call_count, 2)

    def test_watch_sleeps_until_thirty_minutes_before_leaving(self):
        config = {"_watch": self.watch,
                  "departure_targets": {"kaptensgatan": {"label": "kontoret", "minutes": 5}}}
        client = vt.Client(config, {})
        before = vt.parse_time("2026-10-06T14:34:59+02:00")
        boundary = vt.parse_time("2026-10-06T14:35:00+02:00")
        with patch.object(client, "watched_journey", return_value=[self.result]) as fetch, \
                patch.object(client, "journeys") as normal:
            routes = vt.fetch_routes(client, ["C"], None, before)
            fetch.assert_not_called()
            self.assertEqual(vt.render(routes, None, before, "old error", 60, config), ("🚋", "idle"))
            vt.fetch_routes(client, ["C"], None, boundary)
            fetch.assert_called_once()
            normal.assert_not_called()

    def test_manual_watch_refresh_before_warning_window_respects_cache_and_retry(self):
        config = {"_watch": self.watch}
        before = NOW.replace(hour=14, minute=0)
        client = vt.Client(config, {})
        with patch.object(client, "watched_journey", return_value=[self.result]) as fetch, \
                patch.object(vt.time, "time", return_value=before.timestamp()):
            vt.fetch_routes(client, ["C"], None, before, manual=True)
            vt.fetch_routes(client, ["C"], None, before, manual=True)
        fetch.assert_called_once()
        client.state["retry_at"] = before.timestamp() + 600
        with patch.object(client, "watched_journey") as fetch, \
                patch.object(vt.time, "time", return_value=before.timestamp() + 120):
            vt.fetch_routes(client, ["C"], None, before, manual=True)
        fetch.assert_not_called()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config_patch = patch.object(vt, "CONFIG", Path(self.directory.name) / "config.json")
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)
        cache_patch = patch.object(vt, "CACHE", Path(self.directory.name))
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        self.result = journey()
        self.responses = []
        for index, leg in enumerate(self.result["tripLegs"]):
            leg["serviceJourney"]["gid"] = str(index)
            leg["_details_reference"] = f"ref/{index}"
            calls = []
            for endpoint, field in (("origin", "Departure"), ("destination", "Arrival")):
                leg[endpoint]["stopPoint"]["gid"] = f"{index}-{endpoint}"
                calls.append({"stopPoint": copy.deepcopy(leg[endpoint]["stopPoint"]),
                              f"planned{field}Time": leg[endpoint]["plannedTime"]})
            self.responses.append({"tripLegs": [{"serviceJourneys": [{"gid": str(index), "callsOnServiceJourney": calls}]}]})
        self.watch = {"id": "test", "journey": self.result}

    def test_exact_services_refresh_and_cancellation_without_route_search(self):
        self.responses[1]["tripLegs"][0]["serviceJourneys"][0]["callsOnServiceJourney"][0]["isDepartureCancelled"] = True
        client = vt.Client({"_watch": self.watch}, {})
        with patch.object(client, "get", side_effect=self.responses) as request, \
                patch.object(client, "journeys") as search, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()):
            routes = vt.fetch_routes(client, ["C"], None, NOW)
            vt.fetch_routes(client, ["C"], None, NOW)
        search.assert_not_called()
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[0].args[0], "journeys/ref%2F0/details")
        self.assertTrue(routes["C"]["results"][0]["tripLegs"][1]["isCancelled"])
        self.assertTrue(vt.traffic_alerts(routes["C"]["results"], NOW))
        self.assertNotIn("isCancelled", self.result["tripLegs"][1])

    def test_missing_service_is_error_not_another_train(self):
        client = vt.Client({"_watch": self.watch}, {})
        with patch.object(client, "get", return_value={"tripLegs": []}), \
                patch.object(client, "journeys") as search, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()):
            routes = vt.fetch_routes(client, ["C"], None, NOW)
        search.assert_not_called()
        self.assertIn("ValueError", client.state["error"])
        self.assertEqual(routes["C"], {})

    def test_watch_expires_and_never_saves_credentials(self):
        option = vt.journey_options([self.result], NOW)[0]
        self.assertTrue(vt.save_watch({"client_secret": "secret"}, option, NOW))
        watch = vt.current_watch(NOW)
        self.assertIsNotNone(watch)
        self.assertNotIn("client_secret", watch["config"])
        self.assertEqual(watch["config"]["origin"], "Kaptensgatan")
        self.assertIsNone(vt.current_watch(vt.parse_time("2026-10-06T17:00:00+02:00")))
        self.assertIsNone(vt.current_watch(vt.parse_time("2026-10-07T15:00:00+02:00")))
        vt.clear_watch()
        self.assertIsNone(vt.current_watch(NOW))

    def test_in_progress_train_delays_remain_visible(self):
        watched = copy.deepcopy(self.result)
        watched["_watch"] = True
        watched["tripLegs"][1]["destination"]["estimatedTime"] = "2026-10-06T15:35:00+02:00"
        self.assertEqual(len(vt.traffic_alerts([watched], vt.parse_time("2026-10-06T15:22:00+02:00"))), 1)


class CommuteTests(unittest.TestCase):
    def test_fast_progress_never_opens_window(self):
        with patch.object(vt, "Timer") as timer, patch.object(vt.subprocess, "Popen") as spawn:
            with vt.progress("test"):
                pass
        spawn.assert_not_called()
        timer.return_value.cancel.assert_called_once()
        timer.return_value.join.assert_called_once()

    def test_progress_window_is_closed_even_on_failure(self):
        for fails in (False, True):
            with self.subTest(fails=fails), patch.object(vt, "Timer") as timer, \
                    patch.object(vt.subprocess, "Popen") as spawn:
                spawn.return_value.poll.return_value = None
                try:
                    with vt.progress("Hämtar resor…"):
                        timer.call_args.args[1]()
                        if fails:
                            raise ValueError("test")
                except ValueError:
                    pass
                self.assertEqual(spawn.call_args.args[0][:3], ["rofi", "-dmenu", "-p"])
                self.assertIn("Hämtar resor", spawn.return_value.stdin.write.call_args.args[0])
                self.assertEqual(spawn.call_args.args[0][-1], "listview { lines: 1; }")
                self.assertEqual(spawn.call_args.kwargs["stdin"], vt.subprocess.PIPE)
                spawn.return_value.terminate.assert_called_once()
                spawn.return_value.wait.assert_called_once_with(timeout=1)
                self.assertTrue(spawn.return_value.stdin.close.called)

    def test_watch_replaces_background_search_even_outside_regular_window(self):
        result = journey()
        watch = {"id": "watch", "journey": result, "config": {"origin": "A", "destination": "B"}, "via": "all"}
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"client_id": "id", "client_secret": "secret"}))
            with patch.object(vt, "CONFIG", config), patch.object(vt, "CACHE", Path(directory)), \
                    patch.object(vt.sys, "argv", ["vasttrafik"]), \
                    patch.dict(vt.os.environ, {"BLOCK_BUTTON": ""}), \
                    patch.object(vt, "current_watch", return_value=watch), \
                    patch.object(vt, "datetime") as clock, \
                    patch.object(vt.Client, "watched_journey", return_value=[result]) as watched, \
                    patch.object(vt.Client, "journeys") as search, \
                    patch("sys.stdout", new_callable=io.StringIO):
                clock.now.return_value = NOW.replace(hour=14, minute=55)
                clock.fromisoformat.side_effect = datetime.fromisoformat
                vt.main()
            watched.assert_called_once_with(watch)
            search.assert_not_called()

    def test_text_mode_shows_home_and_departure_without_rofi(self):
        result = journey()
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"client_id": "id", "client_secret": "secret"}))
            with patch.object(vt, "CONFIG", config), patch.object(vt, "CACHE", Path(directory)), \
                    patch.object(vt.sys, "argv", ["vasttrafik", "--text"]), \
                    patch.dict(vt.os.environ, {"BLOCK_BUTTON": ""}), \
                    patch.object(vt, "datetime") as clock, \
                    patch.object(vt.Client, "journeys", return_value=[result]), \
                    patch.object(vt, "rofi") as menu, \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                clock.now.return_value = NOW
                clock.fromisoformat.side_effect = datetime.fromisoformat
                clock.fromtimestamp.side_effect = datetime.fromtimestamp
                vt.main()
            menu.assert_not_called()
            self.assertIn("Hemma ≈15:35", output.getvalue())
            self.assertIn("Gå 15:10", output.getvalue())
            self.assertNotIn("#CBE0F0", output.getvalue())

    def test_departure_walk_affects_search_and_cache(self):
        config = {"departure_targets": {"kaptensgatan": {"label": "kontoret", "minutes": 5}}}
        client = vt.Client(config, {})
        with patch.object(client, "journeys", return_value=[]) as search, \
                patch.object(vt.time, "time", return_value=NOW.timestamp()):
            vt.fetch_routes(client, ["C"], None, NOW)
            self.assertEqual(search.call_args.args[1].strftime("%H:%M"), "15:05")
            client.config["departure_targets"]["kaptensgatan"]["minutes"] = 8
            vt.fetch_routes(client, ["C"], None, NOW)
            self.assertEqual(search.call_count, 2)
        option = vt.journey_options([journey()], NOW)[0]
        text = vt.itinerary_text(option, config)
        self.assertIn("Gå 15:02", text)
        self.assertIn("Hemma ≈15:35", text)

    def test_temporary_route_settings_do_not_replace_default(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(vt, "CONFIG", Path(directory) / "config.json"):
            vt.save_route({"origin": "Kaptensgatan", "destination": "Trollhättan resecentrum"}, persist_endpoints=True)
            vt.save_route({"origin": "Ullevi", "destination": "B", "departure_targets": {"ullevi": {"label": "Ullevi", "minutes": 3}}})
            saved = json.loads(vt.CONFIG.with_name("route.json").read_text())
        self.assertEqual(saved["origin"], "Kaptensgatan")
        self.assertEqual(saved["departure_targets"]["ullevi"]["minutes"], 3)

    def test_update_keeps_deadline_and_number_of_alternatives(self):
        selections = ["Framme senast…", "Båda", "17", "Ladda en tidigare", "Uppdatera resorna", None]
        with patch.object(vt, "datetime") as clock, \
                patch.object(vt, "current_watch", return_value=None), \
                patch.object(vt, "rofi", side_effect=selections), \
                patch.object(vt, "load_routes", return_value=({}, None)) as fetch:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            vt.show_journeys({}, {}, None)
        self.assertEqual(fetch.call_args_list[-1], fetch.call_args_list[-2])
        self.assertEqual(fetch.call_args.args[0]["_arrival_before"], 2)

    def test_diagnostics_never_requests_network_or_prints_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"client_id": "private-id", "client_secret": "private-secret"}))
            with patch.object(vt, "CONFIG", config), patch.object(vt, "CACHE", Path(directory)), \
                    patch.object(vt.sys, "argv", ["vasttrafik", "--diagnostics"]), \
                    patch.object(vt.Client, "get") as request, \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                vt.main()
            request.assert_not_called()
            self.assertIsNone(json.loads(output.getvalue())["cache_age_seconds"])
            self.assertNotIn("private", output.getvalue())


class MainTests(unittest.TestCase):
    def test_click_opens_menu_without_network_or_fetch_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"client_id": "test", "client_secret": "test"}))
            with patch.object(vt, "CONFIG", config), patch.object(vt, "CACHE", Path(directory)), \
                    patch.object(vt.sys, "argv", ["vasttrafik", "--menu"]), \
                    patch.object(vt.Client, "get") as request, \
                    patch.object(vt.fcntl, "flock") as lock, \
                    patch.object(vt, "show_journeys") as menu, \
                    patch("sys.stdout", new_callable=io.StringIO):
                vt.main()
            request.assert_not_called()
            lock.assert_not_called()
            menu.assert_called_once()

    def run_main(self, hour):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"client_id": "test", "client_secret": "test"}))
            with patch.object(vt, "CONFIG", config), patch.object(vt, "CACHE", Path(directory) / "cache"), \
                    patch.object(vt, "datetime") as clock, patch.object(vt.sys, "argv", ["vasttrafik"]), \
                    patch.dict(vt.os.environ, {"BLOCK_BUTTON": ""}), \
                    patch.object(vt, "fetch_routes", return_value={}) as fetch, \
                    patch.object(vt, "track_usage") as tracking, \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                clock.now.return_value = NOW.replace(hour=hour)
                vt.main()
                tracking.assert_not_called()
                return fetch.call_count, output.getvalue()

    def test_automatic_window_boundaries(self):
        for hour, calls in [(14, 0), (15, 1), (16, 1), (17, 0)]:
            with self.subTest(hour=hour):
                count, output = self.run_main(hour)
                self.assertEqual(count, calls)
                self.assertEqual(len(output.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
