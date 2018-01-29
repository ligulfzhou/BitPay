# tar zcvf ../app.tar.gz --exclude=.git/ --exclude=__pycache__/ --exclude=.idea/ --exclude=deploy.sh .
# cd ../
# # rsync -azP ../ktv_coupon stage:prj/ktv_coupon
# #scp app.tar.gz stage_dhcp:thunder/myktv_cms/app.tar.gz
# scp app.tar.gz stage:prj/ktv_coupon/app.tar.gz
# 
# ssh stage<< 'END'
#     cd ~/prj/ktv_coupon/
#     tar zxvf app.tar.gz
# END
rsync -azP --exclude=.git ../bitpay aws:source

ssh aws << EOF
svc restart bitpay:bitpay-8100
svc restart bitpay:bitpay-8101
svc restart bitpay:bitpay-8102
svc restart bitpay:bitpay-8103
EOF
