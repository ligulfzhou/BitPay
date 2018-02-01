<html>
    <head>
        <title>
            demo页面
        </title>
    </head>
    <body>

        <div>复制支付字符： bitcoin:?r=https://bitpay.ligulfzhou.com/btc/payment/request/{{order['order_id']}} </div>
        或者扫支付码
        <div id="qrcode"></div>
<br /><br /><br />
        <div>
如何在测试网络测试<br />
1: 获取测试网的比特币： https://testnet.manu.backend.hamburg/faucet<br />
2: 下载electrum： https://electrum.org/#home<br />
3: 将钱包在测试网运行，如electrum   :   open -n /Applications/Electrum.app —args —testnet<br />
4: 将bitcoin:?r=https://bitpay.ligulfzhou.com/btc/payment/request/{{order['order_id']}}复制到收款地址栏<br />
5: 支付后，会收到通知<br />
        </div>

        <script type='text/javascript' src='https://code.jquery.com/jquery-3.3.1.min.js'></script>
        <script type='text/javascript' src='/static/js/qrcode.min.js'></script>
        <script type='text/javascript'>
        $(document).ready(function () {
           var qrcode = new QRCode("qrcode", {
                text: "bitcoin:?r=https://bitpay.ligulfzhou.com/btc/payment/request/{{order['order_id']}}",
                width: 128,
                height: 128,
                colorDark : "#000000",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.H
            });
        })
        </script>
    </body>
</html>
