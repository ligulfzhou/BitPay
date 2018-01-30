<html>
    <head>
        <title>
            demo页面
        </title>
    </head>
    <body>
        <div>
            订单号: </div class='order_id'> </div>
            <button id='generate_order'>商户掉我们这边生成订单号</button>
        </div>

        <div id='order_info'>
                        
        </div>

        <script type='text/javascript' src='https://code.jquery.com/jquery-3.3.1.min.js'></script>
        <script type='text/javascript'>
        $(document).ready(function () {
            $('#generate_order').click(function(){
                $.ajax({
                    url: "/btc/payment/demo/gen/order",
                    data: {},
                    method: "POST",
                    success: function(data) {
                        console.log(data)
                        $('#order_info').html('生成了订单： 订单id:' + data.order_id + '  需要付'+ data.satoshi + ' satoshi' + '<br /> <a href="/btc/payment/demo/invoice/' + data.order_id + '">去支付</a>')
                    }
                });
            })
        })
        </script>
    </body>
</html>
