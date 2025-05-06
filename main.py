import iso20022 as iso
from lxml import etree

# Example usage
if __name__ == '__main__':
    with open ('pain_001.json', "r") as f:
        json_str :str = f.read()
    #end with
    iso_xml_utf8 :bytes = iso.json_to_xml (json_str)
    iso_xml_str_pretty :str = iso.json_to_xml (json_str = json_str, pretty=True)
    print(iso_xml_utf8, iso_xml_str_pretty, sep="\n\n")

    with open("pain.001.001.09.xsd", "rb") as f:
        xsd_doc :etree.ElementTree = etree.parse(f)
        xsd_schema = etree.XMLSchema(xsd_doc)

    # Parse the XML bytes
    try:
        xml_doc :etree.ElementTree = etree.fromstring(iso_xml_str_pretty)
#       with open("test.xml", "rb") as f:
#            xml_doc :etree.ElementTree = etree.parse(f)
    except etree.XMLSyntaxError as e:
        print("\nXML parsing error:", e)
        exit()

    # Validate against the pain.001 schema
    if xsd_schema.validate(xml_doc):
        print("\nXML conforms to XSD schema")
    else:
        print("\nXML does not conform to XSD schema")
        for error in xsd_schema.error_log:
            print(error.message)