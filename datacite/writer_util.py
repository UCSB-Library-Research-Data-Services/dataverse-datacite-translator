import xml.etree.ElementTree as ET
from typing import List


#Writes attribute into XML element
def write_attribute(xml_parent, name, value) -> ET.Element | None:
    if value:
        xml_parent.set(name, value) 
        return xml_parent
    
    return None


#Writes element with name and text
#Implementation Note: We can ommit the lang parameter in the source code since it is always null
def write_full_element(xml_parent, name, value) -> ET.Element | None:
    if value:
        new_element = ET.SubElement(xml_parent, name)
        new_element.text = value
        return new_element

    return None


#Writes an element with name, text, and multiple attributes
def write_full_element_with_attributes(xml_parent, name, attribute_map, value) -> ET.Element | None:
    if value:
        new_element = ET.SubElement(xml_parent, name)
        for attribute_key, attribute_value in attribute_map.items():
            write_attribute(new_element, attribute_key, attribute_value)
        new_element.text = value

        return new_element


    return None


#Writes multiple elements with the same name and a list of differnt text values
def write_full_element_list(xml_parent, name, values) -> list[ET.Element] | None:
    elements = []
    if values:
        for value in values:
            new_element = ET.SubElement(xml_parent, name)
            new_element.text = value
            elements.append(new_element)

    return elements

