#let navy = rgb("183153")
#let blue = rgb("1f5a92")
#let pale-blue = rgb("eaf2f8")
#let pale-gray = rgb("f4f6f8")

#set page(
  paper: "a4",
  margin: (left: 3cm, right: 2cm, top: 2.5cm, bottom: 2.5cm),
  numbering: "1",
  number-align: center + bottom,
  footer: context if counter(page).get().first() > 2 [
    #set text(size: 9pt, fill: rgb("666666"))
    #line(length: 100%, stroke: 0.5pt + rgb("aeb8c2"))
    #v(3pt)
    #grid(
      columns: (1fr, auto),
      [Lab 03 · Bitcoin Script],
      [Trang #counter(page).display("1")],
    )
  ],
)
#set text(font: "Times New Roman", size: 12pt, lang: "vi", fill: rgb("202020"))
#set par(justify: true, leading: 0.72em, first-line-indent: 1.27cm)
#set heading(numbering: "1.")
#show heading: set text(fill: navy)
#show heading.where(level: 1): it => {
  set text(size: 14pt, weight: "bold", fill: navy)
  set par(first-line-indent: 0pt)
  block(above: 1.2em, below: 0.55em, breakable: false)[
    #it
    #v(2pt)
    #line(length: 100%, stroke: 0.8pt + blue)
  ]
}
#show heading.where(level: 2): it => {
  set text(size: 12.5pt, weight: "bold", fill: blue)
  set par(first-line-indent: 0pt)
  block(above: 0.9em, below: 0.35em, breakable: false)[#it]
}
#show table.cell: it => {
  set par(first-line-indent: 0pt, justify: false)
  set text(size: 10.5pt)
  it
}
#show raw: set text(font: "Consolas", size: 9pt)

#set page(numbering: none, footer: none)
#place(top + left, dx: -3cm, dy: -2.5cm, rect(width: 21cm, height: 0.7cm, fill: navy, stroke: none))
#place(bottom + left, dx: -3cm, dy: 2.5cm, rect(width: 21cm, height: 0.45cm, fill: blue, stroke: none))
#align(center)[
  #text(size: 13pt, weight: "bold", fill: navy)[ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH]\
  #text(size: 13pt, weight: "bold", fill: navy)[TRƯỜNG ĐẠI HỌC KHOA HỌC TỰ NHIÊN]\
  #text(size: 12pt, fill: blue)[KHOA CÔNG NGHỆ THÔNG TIN · BỘ MÔN CÔNG NGHỆ TRI THỨC]

  #v(2.7cm)
  #block(width: 100%, inset: (x: 0.8cm, y: 0.75cm), fill: pale-blue, stroke: (left: 4pt + blue))[
    #align(center)[
      #text(size: 12pt, weight: "bold", fill: blue, tracking: 1pt)[BÁO CÁO THỰC HÀNH]\
      #v(0.35cm)
      #text(size: 22pt, weight: "bold", fill: navy)[LAB 03]\
      #v(0.45cm)
      #text(size: 17pt, weight: "bold", fill: navy)[TÌM HIỂU NGÔN NGỮ KỊCH BẢN CỦA BITCOIN]
    ]
  ]

  #v(2.4cm)
]

#align(left)[
  #block(width: 100%, inset: 12pt, fill: pale-gray, radius: 3pt)[
    #set par(first-line-indent: 0pt, leading: 0.9em)
    #grid(
      columns: (4cm, 1fr),
      row-gutter: 7pt,
      [#text(weight: "bold", fill: navy)[Học phần]], [Blockchain],
      [#text(weight: "bold", fill: navy)[Năm học]], [2026],
      [#text(weight: "bold", fill: navy)[Mã nhóm]], [group4],
      [#text(weight: "bold", fill: navy)[Sinh viên thực hiện]], [Phạm Nguyễn Gia Bảo],
    )
  ]
]

#v(1fr)
#align(center)[#text(weight: "bold")[TP. Hồ Chí Minh, tháng 9 năm 2026]]
#pagebreak()

#set page(numbering: "i", footer: none)
#align(center)[
  #text(size: 18pt, weight: "bold", fill: navy)[MỤC LỤC]
  #v(3pt)
  #line(length: 45%, stroke: 1.2pt + blue)
]
#v(0.5cm)
#show outline.entry: it => {
  set text(size: if it.level == 1 { 11.5pt } else { 10.5pt }, weight: if it.level == 1 { "bold" } else { "regular" }, fill: if it.level == 1 { navy } else { rgb("303030") })
  it
}
#outline(title: none, depth: 2)
#pagebreak()
#set page(numbering: "1")
#counter(page).update(1)

= Mục tiêu và phạm vi

Bài thực hành khảo sát cơ chế khóa và mở khóa UTXO bằng Bitcoin Script trên Bitcoin Testnet4. Phạm vi triển khai gồm hai mô hình phổ biến: Pay-to-Public-Key-Hash (P2PKH) và Pay-to-Script-Hash (P2SH) chứa điều kiện đa chữ ký 2-trên-2. Hệ thống hỗ trợ sinh khóa và địa chỉ, truy vấn UTXO, xây dựng giao dịch có phí và đầu ra tiền thừa, ký giao dịch, kiểm tra kịch bản cục bộ và phát giao dịch lên testnet khi người dùng chủ động yêu cầu.

Bitcoin Script là ngôn ngữ dựa trên ngăn xếp, không Turing-complete và không duy trì trạng thái theo mô hình hợp đồng thông minh tổng quát. Một giao dịch hợp lệ khi dữ liệu mở khóa của đầu vào thỏa điều kiện khóa của UTXO được tham chiếu, đồng thời đáp ứng các quy tắc đồng thuận và chính sách tiếp nhận của nút mạng.

= Cấu trúc dự án

Gói nộp bài có thư mục gốc `group4`, bên trong gồm `Code` và `Report.pdf`. Thư mục mã nguồn được tổ chức như sau:

#table(
  columns: (1.3fr, 3fr),
  inset: 5pt,
  stroke: 0.5pt,
  table.header([*Thành phần*], [*Chức năng*]),
  [`task1_p2pkh.py`], [Giao diện dòng lệnh cho quy trình P2PKH],
  [`task2_multisig.py`], [Giao diện dòng lệnh cho quy trình P2SH multisig 2-trên-2],
  [`common/wallet.py`], [Sinh khóa, địa chỉ, redeem script và lưu ví cục bộ],
  [`common/txbuild.py`], [Chọn đầu vào/đầu ra, tính phí và ký giao dịch],
  [`common/scriptcheck.py`], [Xác minh Script trước khi phát giao dịch],
  [`common/network.py`], [Kết nối Esplora Testnet4 và Bitcoin Core tùy chọn],
  [`common/config.py`, `models.py`, `cli.py`], [Cấu hình, mô hình dữ liệu và xử lý CLI dùng chung],
  [`tests/`], [Kiểm thử ví, giao dịch và lớp mạng ở chế độ ngoại tuyến],
)

Khóa riêng được lưu trong `.secrets/wallet.json` tại môi trường cục bộ. Thư mục này, môi trường ảo và tệp tạm được loại khỏi gói nộp để tránh lộ bí mật và giảm kích thước hồ sơ.

= Kiến trúc và nguyên lý hoạt động

== Luồng xử lý tổng quát

Hệ thống gồm bốn lớp: lớp CLI nhận lệnh; lớp ví quản lý khóa và Script; lớp giao dịch xây dựng, ký và kiểm tra; lớp mạng truy vấn UTXO, phát giao dịch và theo dõi xác nhận. Luồng thực hiện tuân theo nguyên tắc _simulate-first_: tạo kế hoạch chi tiêu, xây dựng và ký cục bộ, kiểm tra Script, xem xét kết quả, sau đó mới cho phép broadcast. Nếu được cấu hình với Bitcoin Core Testnet4, `testmempoolaccept` được dùng như một cổng kiểm tra bổ sung trước khi gửi.

Một giao dịch chi tiêu sử dụng UTXO đã xác nhận, tạo đầu ra đến địa chỉ nhận và tạo đầu ra tiền thừa khi phần dư lớn hơn ngưỡng dust. Phí được ước lượng theo satoshi trên virtual byte; hệ thống lặp lại bước ký và điều chỉnh tiền thừa vì độ dài chữ ký DER có thể làm thay đổi kích thước giao dịch. Giao dịch chỉ hợp lệ cục bộ khi `VerifyScript` chấp nhận toàn bộ cặp `scriptSig`–`scriptPubKey`.

== P2PKH

Địa chỉ P2PKH được suy ra từ khóa công khai nén. UTXO được khóa bởi chuỗi thao tác `OP_DUP OP_HASH160 <public-key-hash> OP_EQUALVERIFY OP_CHECKSIG`. Khi chi tiêu, `scriptSig` cung cấp chữ ký ECDSA và khóa công khai. Trình thông dịch sao chép khóa công khai, băm bằng HASH160, so sánh với giá trị đã cam kết và cuối cùng xác minh chữ ký đối với nội dung giao dịch. Vì chỉ một khóa riêng có quyền ký, P2PKH đơn giản và tiết kiệm không gian nhưng tồn tại một điểm lỗi duy nhất.

Quy trình thực hiện gồm: sinh cặp khóa testnet; nhận BTC thử nghiệm vào địa chỉ; truy vấn UTXO; chọn UTXO đủ giá trị; tạo đầu ra nhận và tiền thừa; ký bằng khóa tương ứng; xác minh Script; tùy chọn kiểm tra mempool; phát giao dịch và theo dõi xác nhận.

== P2SH multisig 2-trên-2

Redeem script có dạng `OP_2 <public-key-1> <public-key-2> OP_2 OP_CHECKMULTISIG`. Địa chỉ P2SH cam kết HASH160 của redeem script thay vì công khai toàn bộ điều kiện khóa tại thời điểm nạp tiền. Khi chi tiêu, `scriptSig` phải cung cấp phần tử rỗng `OP_0`, hai chữ ký đúng thứ tự và redeem script. `OP_0` bù cho hành vi lịch sử của `OP_CHECKMULTISIG` khi opcode này lấy thừa một phần tử khỏi ngăn xếp.

Mô hình 2-trên-2 yêu cầu sự đồng thuận của cả hai chủ thể ký. Cơ chế này phù hợp với đồng quản lý tài sản hoặc quy trình phê duyệt kép; đổi lại, giao dịch lớn hơn, phí cao hơn và việc mất một khóa có thể khiến UTXO không còn khả năng chi tiêu.

= Cài đặt và vận hành

Môi trường yêu cầu Python 3.10 trở lên và các thư viện được ghim phiên bản trong `requirements.txt`. Hai chương trình mặc định ẩn WIF; tùy chọn hiển thị khóa chỉ dành cho minh họa có kiểm soát. Endpoint Esplora bắt buộc dùng HTTPS, còn địa chỉ và tham số mạng được cố định ở Bitcoin Testnet4 nhằm hạn chế thao tác nhầm trên mainnet.

Đối với mỗi bài, lệnh `init` tạo hoặc đọc lại ví đã lưu. Sau khi địa chỉ nhận được Testnet4 BTC và có UTXO phù hợp, lệnh `spend` dựng giao dịch ở chế độ dry-run. Kết quả trả về gồm giao dịch thô, txid dự kiến, phí, kích thước, số tiền gửi, tiền thừa và trạng thái xác minh cục bộ. Chỉ khi người dùng thêm `--broadcast`, giao dịch mới được gửi lên mạng; `--wait` tiếp tục theo dõi cho đến khi có xác nhận.

= Kiểm thử và kết quả

== Phương pháp

Kiểm thử ngoại tuyến sử dụng giao dịch và UTXO giả lập để xác minh logic mật mã, cấu trúc Script, tính phí và xử lý lỗi mà không cần faucet. Bộ kiểm thử bao phủ đường đi đúng và các trường hợp âm: ký P2PKH bằng sai khóa, multisig thiếu chữ ký, đầu ra dưới ngưỡng dust, UTXO không đủ và Esplora không dùng HTTPS. Gói nộp cũng được kiểm tra riêng để bảo đảm đúng cấu trúc và không chứa ví hoặc môi trường ảo.

== Kết quả đã xác minh

#table(
  columns: (3fr, 1.2fr),
  inset: 5pt,
  stroke: 0.5pt,
  table.header([*Nhóm kiểm thử*], [*Kết quả*]),
  [Sinh ví P2PKH Testnet4 và P2SH 2-trên-2], [Đạt],
  [Lưu và đọc lại dữ liệu ví], [Đạt],
  [P2PKH với chữ ký hợp lệ], [Đạt],
  [P2PKH ký bằng khóa không tương ứng], [Bị từ chối đúng thiết kế],
  [Multisig đủ hai chữ ký và có `OP_0`], [Đạt],
  [Multisig chỉ có một chữ ký], [Bị từ chối đúng thiết kế],
  [Từ chối đầu ra dust], [Đạt],
  [Chọn UTXO và phân tích phản hồi Esplora], [Đạt],
  [Từ chối endpoint Esplora HTTP], [Đạt],
  [Cấu trúc ZIP và loại trừ bí mật], [Đạt],
)

Tại thời điểm hoàn thiện báo cáo, 16 kiểm thử chức năng và 3 kiểm thử đóng gói đều thành công. Kết quả này chứng minh tính đúng đắn của luồng xây dựng và xác minh giao dịch trong môi trường cục bộ. Báo cáo không khẳng định giao dịch Testnet4 đã được broadcast hoặc xác nhận khi chưa có txid thực tế; việc phát giao dịch phụ thuộc UTXO từ faucet và phải được thực hiện có chủ đích.

== Minh chứng testnet

#table(
  columns: (1.15fr, 3.85fr),
  inset: 4pt,
  stroke: 0.5pt,
  table.header([*Trường*], [*Giá trị và minh chứng*]),
  [P2PKH], [Địa chỉ `moqRhCuPgsmjybRA4krhCZptz65Sb47Pf9` — #link("https://mempool.space/testnet4/address/moqRhCuPgsmjybRA4krhCZptz65Sb47Pf9")[xem trên mempool.space Testnet4]],
  [Funding txid], [Chưa phát sinh; explorer ghi nhận 0 giao dịch và 0 UTXO tại thời điểm kiểm tra],
  [Spend txid], [Chưa phát sinh; chưa thể dựng giao dịch chi tiêu khi chưa có funding UTXO],
  [P2SH 2-trên-2], [Địa chỉ `2N1LrrNXuTaMAGKzRpUnVJHg3DVnUxajsGz` — #link("https://mempool.space/testnet4/address/2N1LrrNXuTaMAGKzRpUnVJHg3DVnUxajsGz")[xem trên mempool.space Testnet4]],
  [Funding txid], [Chưa phát sinh; explorer ghi nhận 0 giao dịch và 0 UTXO tại thời điểm kiểm tra],
  [Spend txid], [Chưa phát sinh; chưa thể dựng giao dịch chi tiêu khi chưa có funding UTXO],
)

Hai URL explorer trên là minh chứng công khai cho trạng thái hiện tại, không phải bằng chứng giao dịch thành công. Sau khi nạp BTC thử nghiệm, người thực hiện phải thay các dòng “Chưa phát sinh” bằng funding txid, spend txid, phí và liên kết dạng `https://mempool.space/testnet4/tx/<txid>`. Không đưa WIF, seed phrase, thông tin RPC hoặc tệp ví vào minh chứng.

= An toàn và đánh giá thiết kế

Các biện pháp chính gồm cô lập khóa trong thư mục không đóng gói, ẩn WIF mặc định, chỉ chấp nhận Testnet4, từ chối endpoint Esplora không mã hóa, kiểm tra Script trước broadcast và hỗ trợ `testmempoolaccept`. Cờ sequence hỗ trợ cơ chế thay thế theo phí; tuy nhiên mọi thay thế hoặc phát lại vẫn cần quyết định của người vận hành.

P2PKH có ưu điểm là phổ biến, dễ kiểm tra và chi phí thấp hơn multisig. Nhược điểm quan trọng là khóa riêng duy nhất trở thành điểm tập trung rủi ro. P2SH multisig phân tán thẩm quyền và tạo bằng chứng phê duyệt kép, nhưng làm tăng kích thước giao dịch, độ phức tạp phối hợp và rủi ro mất khả năng phục hồi trong cấu hình 2-trên-2.

Bitcoin Script có tính xác định, bề mặt thực thi nhỏ và phù hợp với kiểm chứng phân tán. Các giới hạn có chủ đích—không vòng lặp tổng quát, khả năng lưu trạng thái hạn chế và mô hình UTXO—giúp giảm rủi ro thực thi nhưng làm cho các nghiệp vụ phức tạp khó biểu đạt hơn. P2SH cải thiện khả năng triển khai điều kiện chi tiêu mà không làm tăng dữ liệu ở đầu ra nạp tiền, song người chi tiêu vẫn phải công bố redeem script.

= Khó khăn và hướng khắc phục

Khó khăn thứ nhất là mã minh họa trong đề chỉ mô tả ý tưởng, chưa bao gồm truy vấn UTXO, chọn đầu vào, tính phí, tạo tiền thừa và kiểm tra trước broadcast. Hệ thống đã bổ sung các thành phần này thành các mô-đun độc lập để dễ kiểm thử.

Khó khăn thứ hai là phí phụ thuộc kích thước giao dịch, trong khi kích thước lại thay đổi theo chữ ký DER. Cách xử lý là ước lượng lặp, ký lại sau khi điều chỉnh tiền thừa và dành biên an toàn nhỏ để tránh mức phí thực tế thấp hơn yêu cầu.

Khó khăn thứ ba nằm ở quy tắc đặc thù của `OP_CHECKMULTISIG`. Nếu thiếu phần tử rỗng đầu tiên, giao dịch không vượt qua kiểm tra. Trường hợp này được xác nhận bằng kiểm thử dương với `OP_0` và kiểm thử âm khi thiếu chữ ký.

Cuối cùng, testnet phụ thuộc faucet, trạng thái mạng và dịch vụ lập chỉ mục. Vì vậy, hệ thống tách kiểm thử ngoại tuyến khỏi kiểm thử tích hợp; kết quả ngoại tuyến có thể tái lập, còn minh chứng testnet chỉ được ghi nhận khi explorer cung cấp txid và xác nhận thực tế.

= Bài học rút ra

Qua bài thực hành, thành viên hiểu rõ hơn rằng Bitcoin không chuyển số dư giữa các tài khoản mà tiêu thụ UTXO và tạo ra các UTXO mới. Tính hợp lệ của giao dịch phụ thuộc đồng thời vào quyền sở hữu khóa, nội dung giao dịch, điều kiện Script và chính sách tiếp nhận của mạng.

Việc triển khai P2PKH làm rõ mối liên hệ giữa khóa công khai, HASH160, địa chỉ và chữ ký. Bài multisig cho thấy một điều kiện chi tiêu có thể phân tán quyền kiểm soát mà không cần bên trung gian, đồng thời nhấn mạnh chi phí vận hành và yêu cầu phục hồi khóa. Quan trọng hơn, quy trình dry-run, kiểm tra Script và kiểm thử trường hợp lỗi cho thấy an toàn giao dịch phải được xây dựng thành từng cổng kiểm soát, không nên phụ thuộc vào việc kiểm tra thủ công sau khi đã broadcast.

= Kết luận

Hệ thống đã hiện thực đầy đủ hai mô hình Script theo phạm vi bài thực hành, kèm quản lý ví cục bộ, tính phí, tiền thừa, xác minh ngoại tuyến, lớp truy cập testnet và bộ kiểm thử. Thiết kế phân tách trách nhiệm giữa ví, giao dịch, Script và mạng giúp kết quả dễ kiểm tra và mở rộng. Bộ kiểm thử hiện tại xác nhận các điều kiện khóa/mở khóa cốt lõi; bước tích hợp cuối cùng là nạp Testnet4 BTC, broadcast có chủ đích và lưu txid thực tế nếu giảng viên yêu cầu minh chứng trên chuỗi.

= Tài liệu tham khảo

#set par(first-line-indent: 0pt)

1. S. Nakamoto, “Bitcoin: A Peer-to-Peer Electronic Cash System,” 2008. #link("https://bitcoin.org/bitcoin.pdf").
2. A. M. Antonopoulos, _Mastering Bitcoin: Programming the Open Blockchain_, 2nd ed., O’Reilly Media, 2017.
3. Bitcoin Developer Documentation, “Transactions.” #link("https://developer.bitcoin.org/devguide/transactions.html").
4. Bitcoin Developer Reference, “Transactions and Script.” #link("https://developer.bitcoin.org/reference/transactions.html").
5. Bitcoin Wiki, “Script.” #link("https://en.bitcoin.it/wiki/Script").
6. python-bitcoinlib documentation. #link("https://bitcoinpython.readthedocs.io/").
7. Blockstream, “Esplora HTTP API.” #link("https://github.com/Blockstream/esplora/blob/master/API.md").
8. Bitcoin Core RPC, “testmempoolaccept.” #link("https://developer.bitcoin.org/reference/rpc/testmempoolaccept.html").
9. mempool.space, “Bitcoin Testnet4 Explorer.” #link("https://mempool.space/testnet4/").
10. Blockchain Agent Skills, “Bitcoin UTXO & Lightning Patterns,” tài liệu tham chiếu cục bộ trong dự án.


