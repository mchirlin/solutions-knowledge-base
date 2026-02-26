"""Quick script to discover pages on the test-site."""
from gevent import monkey; monkey.patch_all()
import sys, os
sys.path.insert(0, os.path.expanduser("~/repo/appian-locust"))
from appian_locust.appian_client import appian_client_without_locust

client = appian_client_without_locust("https://eng-test-aidc-dev.appianpreview.com")
client.login(auth=["admin.user", "ineedtoadminister"])
client.get_client_feature_toggles()

sites_obj = client.visitor._Visitor__sites
site = sites_obj.get_site_data_by_site_name("test-site")
print("Pages found:", list(site.pages.keys()))
for name, page in site.pages.items():
    print(f"  page_name={name}  type={page.page_type}")

client.logout()
