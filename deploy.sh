tar zcvf ../app.tar.gz --exclude=.git/ --exclude=__pycache__/ --exclude=.idea/ --exclude=deploy.sh .
cd ../
# rsync -azP myktv_cms stage:thunder/myktv_cms
#scp app.tar.gz stage_dhcp:thunder/myktv_cms/app.tar.gz
scp app.tar.gz stage:prj/myktv/app.tar.gz

ssh stage << 'END'
    cd ~/prj/myktv/
    tar zxvf app.tar.gz
END
