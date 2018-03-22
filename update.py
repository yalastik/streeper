import requests
from app import db
import models

def run():
    channels = models.Channel.query.all()
    for row in channels:
        try:
            r = requests.get(
                'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getChatMembersCount?chat_id=%s' % row.link)
            if not r.json()['ok']:
                db.session.delete(row)
            else:

                up_todate_name = requests.get(
                    'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getChat?chat_id=%s' % row.link).json()['result']['title']

        #         up_todate_pic = requests.get(
        #     'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getChat?chat_id=%s' % row.link).json()['result']['photo']['small_file_id']

        #         file_path = requests.get(
        #     'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getFile?file_id=%s' % up_todate_pic
        # ).json()['result']['file_path']



        #         url = 'https://api.telegram.org/file/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/%s' % file_path
        #         wget.download(url, os.path.dirname(__file__) + '/static/images/channel_icons/' + "{}.jpg".format(row.link))

        #         row.image = "{}.jpg".format(row.link)


                row.name = up_todate_name

                up_todate_subscribers = requests.get(
                    'https://api.telegram.org/bot435931033:AAHtZUDlQ0DeQVUGNIGpTFhcV1u3wXDjKJY/getChatMembersCount?chat_id=%s' % row.link).json()['result']
                row.subscribers = up_todate_subscribers
        except:
            pass

        db.session.commit()
    print("Database has been updated!")

if __name__ == '__main__':
    run()

