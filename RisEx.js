// RIS Extractor -- Copyright (C) 2012  Claire Xenia Wolf <claire@yosyshq.com>
// Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)
// vim: set expandtab:
//
// JavaScript-Code zum umformatieren einer RIS "Gesamte Rechtsvorschrift" Seite,
// zum besseren Text-export durch copy&paste vom Browser zu einem Editor.
//
// ANLEITUNG:
// 1. Öffne die RIS Seite für eine "Gesammte Rechtsvorschrift"
// 2. Öfffne die JavaScript console (Crtl+Shift+J in manchen Browsern)
// 3. Kopiere den untenstehenden Code in die JavaScript console
// 4. Drücke ENTER und sehe dem Script bei der arbeit zu
// 5. Clicke auf die Seite und kopiere den Inhalt (Ctrl+A und dann Ctrl+C)
// 6. Erstelle ein neues Text-File im editor und füge ein (Ctrl+V)
// 7. Überprüfe (und ggf. korrigiere) das Ergebnis und speichere das File 

// RisEx (RIS Extractor)
RisEx = {
    removeElementsOfClassLoop(className) {
            console.log("Removing all elements of '" + className + "' class.");
            while (1) {
                    elements = document.getElementsByClassName(className);
                    if (elements.length == 0) break;
                    console.log("Removing " + elements.length + " elements.");
                    for (let el of elements) el.remove();
            }
            console.log("Finished removeOnlyScreenreaderElements().");
    },

    replaceBodyWithContentBlocks() {
            console.log("Replacing top-level body content.");
            title = document.getElementById("Title");
            blocks = document.getElementsByClassName("contentBlock");
            console.log("Removing first two blocks.");
            // blocks[0].remove(); blocks[0].remove();
            console.log("Using the " + blocks.length + " remaining blocks.");
            document.body.replaceChildren(title, ...blocks);
            console.log("Finished replaceBodyWithContentBlocks().");
    },

    replaceAllImagesWithNotes() {
            elements = document.getElementsByClassName("AbbildungoderObjekt");
            for (let el of elements)
                    el.innerText = "Anm.: Diese Abbildung ist im TXT-Export nicht enthalten."
    },

    addLineBreakBeforeElementsByTagName(tagName) {
            console.log("Adding line breaks before all '" + tagName + "' elements.");
            elements = document.getElementsByTagName(tagName);
            console.log("Adding a line break before " + elements.length + " elements.");
            for (let el of elements)
                    el.insertAdjacentHTML("beforebegin", "<br/>");
            console.log("Finished addLineBreakBeforeElementsByTagName().");
    },

    go() {
            this.removeElementsOfClassLoop("onlyScreenreader");
            this.removeElementsOfClassLoop("sr-only");
            this.replaceBodyWithContentBlocks();
            this.removeElementsOfClassLoop("Kursiv");
            this.replaceAllImagesWithNotes();
            this.addLineBreakBeforeElementsByTagName("h4");
            return "==== RIS Rewriter Finished ====";
    },

    // highlight blocks on hover and remove blocks on double clicks
    edit() {
        blocks = document.getElementsByClassName("contentBlock");
        for (b of blocks) {
            b.onmouseover  = function(ev) {
                let el = ev.currentTarget;
                // console.log("Enter:", el);
                el.style.backgroundColor = "#aaa";
            };
            b.onmouseleave = function(ev) {
                let el = ev.currentTarget;
                // console.log("Leave:", el);
                el.style.backgroundColor = "";
            };
            b.ondblclick = function(ev) {
                let el = ev.currentTarget;
                el.remove();
            };
        }
    },

    // disable the edit() magic
    noedit() {
        blocks = document.getElementsByClassName("contentBlock");
        for (b of blocks) {
            b.onmouseover  = "";
            b.onmouseleave = "";
            b.ondblclick = "";
        }
    },
};

// Short alias for ease of use
let rx = RisEx;

// Run this to perform the main transformation
rx.go();

// Run this to enter edit mode:
//   - hover highlights blocks
//   - double click removes blocks
// (Works before and after rx.go())
rx.edit();

// Run this to disable edit mode again
// rx.noedit();
