import html5lib
import xmljson

def xml_to_json(element):
    return {'tag': element.tag,
            'attributes': element.attrib,
            'children': [xml_to_json(e) for e in element]}

def parse_html_to_json(test_html):
    xml_document = html5lib.parse(test_html, namespaceHTMLElements=False)
    dom_document = xml_to_json(xml_document)
    return dom_document


import dukpy

class DukPyInterpreter(object):
    def __init__(self):
        self.interpreter = dukpy.JSInterpreter()
        
        # Multiple loggers possible with: new Duktape.Logger('logger name')
        logger_init = "var logger = new Duktape.Logger();"
        self.interpret(logger_init)
    
    def interpret(self, javascript, **kwargs):
        # TODO: This is not really correct, because the kwargs will only be
        # assessible as 'dukpy['key']', rather than just by reference ot 'key',
        # so you really need to do a kind of:
        # var key = dukpy['key'];
        # For each of them.
        return self.interpreter.evaljs(javascript, **kwargs)

    def load_document(self, document):
        javascript = "var document = dukpy['document'];"
        self.interpret(javascript, document=document)

from py_mini_racer import py_mini_racer
import json

class PyMiniRacerInterpreter(object):
    def __init__(self):
        self.interpreter = py_mini_racer.MiniRacer()
    
    def interpret(self, javascript, **kwargs):
        # This ignores the kwargs, we should do something like:
        # "var key = {};".format(json.dumps(value)
        # And interpret that first
        return self.interpreter.eval(javascript)

    def load_document(self, document):
        javascript = "var document = {};".format(json.dumps(document))
        self.interpret(javascript)

import pytest
# Might want to have 'scope="session"' or 'scope="module"'
@pytest.fixture(params=[DukPyInterpreter, PyMiniRacerInterpreter],
                ids=['dukpy', 'mini-racer'])
def interpreter(request):
    javascript_interpreter = request.param()
    return javascript_interpreter


def test_javascript(interpreter):
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
    interpreter.interpret(javascript)
    # assert that the new element is indeed in the dom




def test_dom(interpreter):
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
    dom_document = parse_html_to_json(test_html)

    dom_javascript = """
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
    interpreter.load_document(dom_document)
    interpreter.interpret(dom_javascript)
    
    expected_paragraph = {'tag': 'p', 'children': [], 'attributes': {'id': 'paragraph-id'}}
    collected_paragraph = interpreter.interpret('collected_paragraph')
    assert collected_paragraph == expected_paragraph
