import json
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom

_conf = {
    "iso_msgType": {
        "customer_credit_transfer_initiation": {
            "isoCd" : "pain.001",
            "latestVer" : "001.09"
        }
    },

    "keyword" : {
        "account" : "Acct"
        ,"address" : "Adr",
        "agent": "Agt",
        "amount" : "Amt",

        "bicfi" : "BICFI",
        "building" : "Bldg",

        "charges": "Chrgs",
        "clearing" : "Clr",
        "country": "Ctry",
        "code" : "Cd",
        "creation": "Cre",
        "creditor": "Cdtr",
        "currency" : "Ccy",
        "customer": "Cstmr",
        "credit": "Cdt",

        "date": "Dt",
        "debtor": "Dbtr",
        "details": "Dtls",
        "document": "Doc",

        "electronic": "Elctrnc",
        "execution": "Exctn",

        "financial" : "Fin",

        "group" : "Grp",

        "iban" : "IBAN",
        "institution" : "Instn",
        "Information": "Inf",

        "header": "Hdr",

        "identification" : "Id",
        "information" : "Inf",
        "initiating": "Initg",
        "initiation": "Initn",
        "instructed" : "Instd",
        "instruction" : "Instr",
        "intermediary" : "Intrmy",
        "issuer" : "Issr",

        "level" : "Lvl",
        "location": "Lctn",
            
        "member" : "Mmb",
        "message" : "Msg",
        "method": "Mtd",

        "name": "Nm",
        "number": "Nb",

        "organisation" : "Org",
        "other" : "Othr",

        "party": "Pty",
        "payment": "Pmt",
        "place": "Plc",
        "post" : "Pst",
        "postal": "Pstl",
        "private" : "Prvt",
        "proprietary": "Prtry",
        "purpose": "Purp",

        "referred": "Rfrd",
        "related": "Rltd",
        "remittance": "Rmt",
        "requested" : "Reqd",

        "scheme" : "Schme",
        "service" : "Svc",
        "street": "Strt",
        "structured": "Strd",
        "system": "Sys",

        "time": "Tm",
        "town" : "Twn",
        "transaction": "Tx",
        "transactions": "Txs",
        "transfer": "Trf",
        "type" : "Tp",

        "ultimate": "Ultmt",
        "unstructured": "Ustrd"
    }
}

def _create_elem (key :str, keyword_dict :dict):
    # Sanitize the key so that it contains valid chars for an XML tag
    sanitized_key = re.sub(r'[^a-zA-Z0-9_.-]', '_', key)
    if not (re.search(r'^[a-zA-Z_]', sanitized_key)) or sanitized_key.lower().startswith('xml'):
        sanitized_key = '_' + sanitized_key
    #end if
    # Now, we map the sanitized_key
    key_items = sanitized_key.split("_")
    mapped_tag = ""
    for key_item in key_items:
        match :re.Match = re.search (r"[1-9][0-9]*$",key_item) # Check whether it ends with a number >= 1
        if match:
            key_item_woNb = key_item [:match.start()]
            mapped_tag += keyword_dict.get(key_item_woNb, key_item_woNb.capitalize())
            mapped_tag += key_item[match.start():] # Append the number
        else:
            mapped_tag += keyword_dict.get(key_item, key_item.capitalize())
        #end if
    #end for
    return ET.Element(mapped_tag)

def _build_xml_elem(key :str, value, keyword_dict :dict):
    elem = _create_elem (key, keyword_dict)
    for k, v in value.items():    
        if isinstance (v, dict):
            if k.endswith('amount'):
                keys = list(v.keys())
                if len(keys)== 2 and "currency" in keys and "amount" in keys:
                    amt_elem = _create_elem (k, keyword_dict)
                    amt_elem.set ('Ccy', v['currency'])
                    amt_elem.text = str(v['amount'])
                    elem.append(amt_elem)
                    return elem
                #end if
            #end if
            child_elem = _build_xml_elem(k, v, keyword_dict)
            elem.append(child_elem)
        elif isinstance(v, list):
            for item_value in v:
                child_elem = _create_elem (k, keyword_dict)
                if isinstance (item_value, dict):
                    child_elem = _build_xml_elem(k, item_value, keyword_dict)
                else:
                    child_elem.text = str(item_value)
                #end if
                elem.append(child_elem)
            #end for
        else:
            child_elem = _create_elem (k, keyword_dict)
            child_elem.text = str(v)
            elem.append(child_elem)
        #end if
    #end for
    return elem

def json_to_xml ( json_str :str, pretty :bool = False) -> bytes | str:
    iso_msgType :dict = _conf['iso_msgType']
    dict_data = json.loads(json_str)
    
    # Extract the ISO Message Type from the 1st key in dict_data
    # E.g. customer_credit_transfer_initiation_v09. Note that there may be a version number at the end.
    header :str = list(dict_data.keys())[0]
    match = re.search(r'_v[0-9]+$',header) # Look for a version number
    msgType_name :str = header[:match.start()] if match else header
    if not (msgType_name in iso_msgType):
        raise ValueError
    #end if
    msgType_ver :str = f"001.{header[match.start()+2:]}" if match else f"001.{iso_msgType[msgType_name]['latestVer']}"
    msgType_isoCd :str = iso_msgType[msgType_name]['isoCd']
    root_elem = ET.Element('Document', xmlns=f"urn:iso:std:iso:20022:tech:xsd:{msgType_isoCd}.{msgType_ver}")
    msg_elem = _build_xml_elem(msgType_name, dict_data[header], _conf['keyword'])
    root_elem.append (msg_elem)
    
    xmlDoc_bytes :bytes = ET.tostring(root_elem, encoding="utf-8", xml_declaration=True)
    return xmlDoc_bytes if not pretty else xml.dom.minidom.parseString(xmlDoc_bytes).toprettyxml()