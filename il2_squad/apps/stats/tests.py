from django.test import TestCase
from .models import PlayerOccurrence, IL2StatsServer, SomePilot
import datetime
from django.utils.timezone import make_aware


class PlayerOccurrenceTestCase(TestCase):

    def setUp(self):
        """
        Set up a test environment for the PlayerOccurrence model.
        """
        self.players = []
        self.server = None
        self.player_cnt = 20
        self.sample_cnt = 50
        # Timestamp for the mean time
        self.mean_ts = make_aware(datetime.datetime(2020, 6, 1, 12, 0, 0))

        # Create a test server
        self.server = IL2StatsServer.objects.create(
            name="Test Server",
            url="http://test-server.com",
        )

        # Create test pilots
        for i in range(self.player_cnt):
            self.players.append(
                SomePilot.objects.create(
                    site=self.server,
                    id_on_site=1000 + i,
                )
            )

        # Create 25 samples
        for i in range(self.sample_cnt):
            PlayerOccurrence.objects.create(
                pilot=self.players[i % self.player_cnt],
                server=self.server,
                coalition="red" if i % 2 == 0 else "blue",
                timestamp=self.mean_ts + datetime.timedelta(seconds=i),
            )

    def test_closest_timestamp(self):
        """
        Test the closest_timestamp method of the PlayerOccurrence model.
        """
        # Exact timestamp
        closest = PlayerOccurrence.closest_timestamp(self.server, self.mean_ts)
        self.assertEqual(closest, self.mean_ts)
        # 1h before should find the oldest
        closest = PlayerOccurrence.closest_timestamp(self.server, self.mean_ts - datetime.timedelta(hours=1))
        self.assertEqual(closest, self.mean_ts)
        # 1h after should find the newest
        closest = PlayerOccurrence.closest_timestamp(self.server, self.mean_ts + datetime.timedelta(hours=1))
        self.assertEqual(closest, self.mean_ts + datetime.timedelta(seconds=self.sample_cnt - 1))
        # 10 seconds after the first should find the one 10 seconds after
        closest = PlayerOccurrence.closest_timestamp(self.server, self.mean_ts + datetime.timedelta(seconds=10))
        self.assertEqual(closest, self.mean_ts + datetime.timedelta(seconds=10))

    def test_player_cnt_at(self):
        """
        Test the player_cnt_at method of the PlayerOccurrence model.
        """
        # At the mean timestamp, we should have half the players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts)
        self.assertEqual(cnt, self.player_cnt // 2)
        # At the first timestamp, we should have all players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=1))
        self.assertEqual(cnt, self.player_cnt)
        # At the last timestamp, we should have all players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=self.sample_cnt - 1))
        self.assertEqual(cnt, self.player_cnt)
        # At a timestamp 1h before the first, we should have 0 players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts - datetime.timedelta(hours=1))
        self.assertEqual(cnt, 0)
        # At a timestamp 1h after the last, we should have 0 players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(hours=1))
        self.assertEqual(cnt, 0)
        # At a timestamp 10 seconds after the first, we should have 1 player
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=10))
        self.assertEqual(cnt, 1)
        # At a timestamp 10 seconds before the last, we should have all players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=self.sample_cnt - 10))
        self.assertEqual(cnt, self.player_cnt)
        # At a timestamp 10 seconds after the last, we should have 0 players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=self.sample_cnt))
        self.assertEqual(cnt, 0)
        # At a timestamp 10 seconds before the first, we should have 0 players
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts - datetime.timedelta(seconds=10))
        self.assertEqual(cnt, 0)
        # At a timestamp 10 seconds after the first, we should have 1 player
        cnt = PlayerOccurrence.player_cnt_at(self.server, self.mean_ts + datetime.timedelta(seconds=10))
        self.assertEqual(cnt, 1)
        # At a timestamp 10