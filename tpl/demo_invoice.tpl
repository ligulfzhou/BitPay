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
