# Mã nguồn — Bitcoin Script Lab

CLI Python này triển khai quy trình P2PKH legacy và multisig P2SH 2-trên-2 trên Bitcoin **Testnet4**. Mặc định chương trình chỉ xây dựng, ký và kiểm tra giao dịch cục bộ; chỉ broadcast khi người dùng truyền rõ tùy chọn `--broadcast`.

Hướng dẫn cài đặt, toàn bộ câu lệnh vận hành, kế hoạch test và bảng minh chứng báo cáo nằm trong [`../README.md`](../README.md).

## Cài đặt nhanh (PowerShell)

Chạy tại thư mục `code/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`python-bitcoinlib` cần OpenSSL. Trên Windows, lớp tương thích đi kèm tự dò bản `libcrypto-3` hiện đại, bao gồm Git for Windows.

## Bài 1 — P2PKH

```powershell
.\.venv\Scripts\python.exe task1_p2pkh.py init
# Nạp Testnet4 BTC vào địa chỉ được hiển thị, rồi dry-run:
.\.venv\Scripts\python.exe task1_p2pkh.py spend <DIA_CHI_TESTNET_DICH> 10000 --fee-rate 2
# Chỉ broadcast sau khi đã xem và xác minh đầu ra:
.\.venv\Scripts\python.exe task1_p2pkh.py spend <DIA_CHI_TESTNET_DICH> 10000 --fee-rate 2 --broadcast --wait
```

Chỉ dùng `init --show-private-key` nếu giảng viên yêu cầu minh họa WIF. Không đưa khóa vào ảnh chụp, báo cáo, Git hoặc ZIP nộp bài.

## Bài 2 — Multisig P2SH 2-trên-2

```powershell
.\.venv\Scripts\python.exe task2_multisig.py init
# Nạp Testnet4 BTC vào địa chỉ P2SH, rồi dry-run:
.\.venv\Scripts\python.exe task2_multisig.py spend <DIA_CHI_TESTNET_DICH> 10000 --fee-rate 2
.\.venv\Scripts\python.exe task2_multisig.py spend <DIA_CHI_TESTNET_DICH> 10000 --fee-rate 2 --broadcast --wait
```

Unlocking script là `OP_0 <sig1> <sig2> <redeemScript>`. `OP_0` bù cho lỗi lịch sử khiến `OP_CHECKMULTISIG` lấy thừa một phần tử trên stack.

## Cấu hình trước khi chạy

- `BTC_LAB_RPC_URL=http://user:password@127.0.0.1:48332`: bật `testmempoolaccept` của Bitcoin Core chạy với `-testnet4`. Chương trình kiểm tra genesis hash và từ chối RPC Testnet3. Thông tin xác thực chỉ được xử lý cục bộ và không in ra.
- `BTC_LAB_ESPLORA_URL`: ghi đè endpoint mặc định `https://mempool.space/testnet4/api`; bắt buộc HTTPS.
- `BTC_LAB_FEE_RATE`: phí mặc định theo sat/vB.
- `BTC_LAB_SECRETS_DIR`: đổi thư mục lưu khóa cục bộ.

CLI luôn chạy `VerifyScript` cục bộ. Khi RPC được cấu hình, chương trình còn kiểm tra Core đang ở chain `test`, đã đồng bộ và chấp nhận raw transaction trước khi broadcast.

## An toàn

- Chỉ dùng testnet; địa chỉ/WIF mainnet legacy không hợp lệ với tham số mạng đã chọn.
- Khóa nằm tại `../.secrets/wallet.json`, bị `.gitignore` và trình đóng gói loại trừ.
- `--replace` làm mất tham chiếu cục bộ đến khóa cũ; không dùng nếu địa chỉ cũ còn tiền.
- Chỉ sử dụng faucet và địa chỉ đích do nhóm kiểm soát.

