import html5lib
import dukpy

def test_javascript():
    test_html = """
    <!DOCTYPE>
    <html><head><title>Hello</title></head>
    <body>
    <h1>I am a title</h1>
    <script type="text/javascript">
    var para = document.createElement("p");
    var node = document.createTextNode("This is new.");
    para.appendChild(node);

    var element = document.getElementById("div1");
    element.appendChild(para);
    </script>
    </body>
    </html>
    """
    document = html5lib.parse(test_html)
    # Assert that the original element is in the dom, and probably that the
    # new element that we expect to be there after the javascript has run is not.
    javascript = "\n".join(script_tag.text for script_tag in document.findall('script'))
    dukpy.evaljs(javascript)
    # assert that the new element is indeed in the dom


import xmljson
import json

def xml_to_json(element):
    return {'tag': element.tag,
            'attributes': element.attrib,
            'children': [xml_to_json(e) for e in element]}


def test_dom():
    test_html = """
    <!DOCTYPE>
    <html>
       <head><title>Hello</title></head>
       <body>
         <div id="first-div"></div>
         <h1>I am a title</h1>
         <div id="second-div"></div>
       </body>
    </html>
    """
    xml_document = html5lib.parse(test_html, namespaceHTMLElements=False)
    dom_document = xml_to_json(xml_document)
    print(json.dumps(dom_document))

    dom_javascript = """
        var logger = new Duktape.Logger();  // or new Duktape.Logger('logger name')
        var document = dukpy['document'];
        document.createElement = function(tag_name){
            function appendChild(element){
                this.children.append(element);
            }
            return {tag: tag_name, attributes: {}, children: []};
        };
        document.getElementById = function(tag_id){
            var find_element = function(element){
                if ('attributes' in element && 'id' in element.attributes && element.attributes.id == tag_id){
                    return element;
                }
                for (var index = 0; index < element.children.length; index++){
                    var child = element.children[index];
                    var recursive_result = find_element(child);
                    if (recursive_result != null){
                        return recursive_result;
                    }
                }
                return null;
            }
            return find_element(document);
        };
        var paragraph = document.createElement('p');
        var paragraph_id = 'paragraph-id'
        paragraph.attributes.id = paragraph_id;
        var div = document.getElementById('first-div');
        div.children.push(paragraph);
        var collected_paragraph = document.getElementById(paragraph_id);
    """
    interpreter = dukpy.JSInterpreter()
    interpreter.evaljs(dom_javascript, document=dom_document)
    
    expected_paragraph = {'tag': 'p', 'children': [], 'attributes': {'id': 'paragraph-id'}}
    collected_paragraph = interpreter.evaljs('collected_paragraph')
    assert collected_paragraph == expected_paragraph
