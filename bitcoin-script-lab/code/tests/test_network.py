from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from common.models import UTXO
from common.config import ESPLORA_URL, NETWORK
from common.network import BitcoinCoreClient, EsploraClient, NetworkError, choose_utxo


class NetworkTests(unittest.TestCase):
    def test_defaults_to_testnet4(self) -> None:
        self.assertEqual(NETWORK, "testnet4")
        self.assertEqual(ESPLORA_URL, "https://mempool.space/testnet4/api")

    def test_choose_smallest_sufficient_utxo(self) -> None:
        items = [UTXO("11" * 32, 0, 30_000), UTXO("22" * 32, 1, 10_000)]
        self.assertEqual(choose_utxo(items, 9_000).value, 10_000)

    @patch("common.network.requests.Session.request")
    def test_esplora_parses_and_filters_utxos(self, request: Mock) -> None:
        response = Mock(ok=True)
        response.json.return_value = [
            {"txid": "11" * 32, "vout": 0, "value": 1234, "status": {"confirmed": True, "block_height": 42}},
            {"txid": "22" * 32, "vout": 1, "value": 9999, "status": {"confirmed": False}},
        ]
        request.return_value = response
        result = EsploraClient().get_utxos("mtest")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].block_height, 42)

    def test_rejects_plain_http_esplora(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            EsploraClient("http://example.test/api")

    def test_no_sufficient_utxo_is_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "No confirmed UTXO"):
            choose_utxo([UTXO("11" * 32, 0, 1_000)], 2_000)

    def test_core_rpc_rejects_testnet3_genesis(self) -> None:
        client = BitcoinCoreClient("http://localhost:18332")
        client.call = Mock(
            side_effect=[
                {"chain": "test", "initialblockdownload": False},
                "000000000933ea01ad0ee984209779baae8c49c84b3e6f9c202b8e9a2a117614",
            ]
        )
        with self.assertRaisesRegex(NetworkError, "not connected to Testnet4"):
            client.test_mempool_accept("00")

    @patch("common.network.time.sleep")
    def test_wait_for_confirmation_is_available(self, sleep: Mock) -> None:
        client = EsploraClient()
        client.transaction_status = Mock(side_effect=[{"confirmed": False}, {"confirmed": True}])
        result = client.wait_for_confirmation("11" * 32, timeout=1, poll_seconds=0)
        self.assertTrue(result["confirmed"])
        sleep.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
