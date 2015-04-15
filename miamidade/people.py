from pupa.scrape import Scraper
from pupa.scrape import Person

import lxml.html
class MiamidadePersonScraper(Scraper):

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def scrape(self):
        (council, ) = tuple(self.jurisdiction.get_organizations())
        yield from self.get_people(council)
        #committees can go in here too


    def get_people(self,council):
        people_base_url = "http://miamidade.gov/wps/portal/Main/government"
        doc = self.lxmlize(people_base_url)
        person_list = doc.xpath("//div[contains(@id,'elected')]//span")
        titles = ["Chairman","Vice Chair"]
        for person in person_list:
            info = person.text_content().strip().split("\n")
            position = info[0].strip()
            name = " ".join(info[1:])
            for title in titles:
                name = name.replace(title,"")
            name = name.strip()
            url = person.xpath(".//a[contains(text(),'Website')]/@href")[0]
            image = person.xpath(".//img/@src")[0]
            pers = Person(name=name,
                            image=image)
            pers.add_source(people_base_url, note="Miami-Dade government website")
            pers.add_source(url, note="individual's website")

            #the commissioners have consistent site format
            if "district" in position.lower():
                person_doc = self.lxmlize(url)
                contact_rows = person_doc.xpath("//div[@class='leftContentContainer']//p")
                for line in contact_rows:
                    line_text = line.text_content()
                    if "email" in line_text.lower():
                        email_address = line_text.replace("Email:","").strip()
                        pers.add_contact_detail(type="email",
                                                value=email_address)
                        continue
                    try:
                        office,phone,fax = line_text.strip().split("\n")
                    except ValueError:
                        #ick, it's all on one line.
                        if "downtown office" in line_text.lower():
                            office = "Downtown Office"
                        elif "district office" in line_text.lower():
                            office = "District Office"
                        else:
                            continue
                        phone = line_text[15:27]
                        fax = line_text[33:45]

                    if "office" not in office.lower():
                        continue
                        #social is also available in here
                        #but I don't see a place to put it
                    phone = phone.replace("Phone","").strip()
                    fax = fax.replace("Fax","").strip()
                    pers.add_contact_detail(type="voice", #phone is not allowed ????
                            value=phone,
                            note=office.strip())

                    pers.add_contact_detail(type="fax", #phone is not allowed ????
                            value=fax,
                            note=office.strip())

            pers.add_membership(organization=council,
                        role=position)

            yield pers