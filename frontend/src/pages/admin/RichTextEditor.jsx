import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import { useEffect } from "react";
import {
  Bold, Italic, List, ListOrdered, Quote, Heading2, Heading3, Heading4,
  Link as LinkIcon, Image as ImageIcon, Undo2, Redo2, Minus,
} from "lucide-react";
import { adminUpload } from "../../lib/api";
import { mediaUrl } from "../../lib/media";

function resolveEditorHtml(html) {
  if (!html?.trim()) return html || "";
  const doc = new DOMParser().parseFromString(html, "text/html");
  doc.querySelectorAll("img[src]").forEach((img) => {
    img.setAttribute("src", mediaUrl(img.getAttribute("src")));
  });
  return doc.body.innerHTML;
}

const ToolBtn = ({ onClick, active, disabled, title, children, testid }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    title={title}
    data-testid={testid}
    className={`p-2 rounded transition-colors ${
      active ? "bg-navy-600 text-white" : "text-slate-700 hover:bg-slate-100"
    } disabled:opacity-40 disabled:cursor-not-allowed`}
  >
    {children}
  </button>
);

export default function RichTextEditor({ value, onChange, placeholder = "Scrivi qui il contenuto…" }) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3, 4] } }),
      Link.configure({ openOnClick: false, HTMLAttributes: { rel: "noopener noreferrer", target: "_blank" } }),
      Image,
      Placeholder.configure({ placeholder }),
    ],
    content: resolveEditorHtml(value || ""),
    onUpdate({ editor }) {
      onChange?.(editor.getHTML());
    },
  });

  useEffect(() => {
    if (editor && value !== undefined) {
      const resolved = resolveEditorHtml(value || "");
      if (resolved !== editor.getHTML()) {
        editor.commands.setContent(resolved, false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editor]);

  if (!editor) return null;

  const addLink = () => {
    const prev = editor.getAttributes("link").href || "";
    const url = window.prompt("URL del link:", prev);
    if (url === null) return;
    if (url === "") {
      editor.chain().focus().unsetLink().run();
      return;
    }
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  };

  const addImage = async () => {
    const choice = window.prompt("Inserisci URL immagine, oppure scrivi 'upload' per caricare un file:");
    if (!choice) return;
    if (choice.toLowerCase() === "upload") {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/*";
      input.onchange = async () => {
        const f = input.files?.[0];
        if (!f) return;
        try {
          const res = await adminUpload(f);
          editor.chain().focus().setImage({ src: res.url }).run();
        } catch (e) {
          alert("Errore upload: " + (e?.response?.data?.detail || e.message));
        }
      };
      input.click();
    } else {
      editor.chain().focus().setImage({ src: choice }).run();
    }
  };

  return (
    <div className="border border-slate-300 rounded-md bg-white overflow-hidden" data-testid="rich-text-editor">
      <div className="flex flex-wrap items-center gap-1 px-3 py-2 border-b border-slate-200 bg-slate-50 sticky top-0 z-10">
        <ToolBtn onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} active={editor.isActive("heading", { level: 1 })} title="Titolo" testid="editor-h1"><Heading2 className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} active={editor.isActive("heading", { level: 2 })} title="Heading 2" testid="editor-h2"><Heading2 className="h-4 w-4 scale-90"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} active={editor.isActive("heading", { level: 3 })} title="Heading 3" testid="editor-h3"><Heading3 className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleHeading({ level: 4 }).run()} active={editor.isActive("heading", { level: 4 })} title="Heading 4" testid="editor-h4"><Heading4 className="h-4 w-4"/></ToolBtn>
        <div className="w-px h-6 bg-slate-300 mx-1" />
        <ToolBtn onClick={() => editor.chain().focus().toggleBold().run()} active={editor.isActive("bold")} title="Grassetto" testid="editor-bold"><Bold className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleItalic().run()} active={editor.isActive("italic")} title="Corsivo" testid="editor-italic"><Italic className="h-4 w-4"/></ToolBtn>
        <div className="w-px h-6 bg-slate-300 mx-1" />
        <ToolBtn onClick={() => editor.chain().focus().toggleBulletList().run()} active={editor.isActive("bulletList")} title="Lista" testid="editor-ul"><List className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleOrderedList().run()} active={editor.isActive("orderedList")} title="Lista numerata" testid="editor-ol"><ListOrdered className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().toggleBlockquote().run()} active={editor.isActive("blockquote")} title="Citazione" testid="editor-quote"><Quote className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().setHorizontalRule().run()} title="Linea orizzontale" testid="editor-hr"><Minus className="h-4 w-4"/></ToolBtn>
        <div className="w-px h-6 bg-slate-300 mx-1" />
        <ToolBtn onClick={addLink} active={editor.isActive("link")} title="Link" testid="editor-link"><LinkIcon className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={addImage} title="Immagine" testid="editor-image"><ImageIcon className="h-4 w-4"/></ToolBtn>
        <div className="w-px h-6 bg-slate-300 mx-1" />
        <ToolBtn onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()} title="Annulla" testid="editor-undo"><Undo2 className="h-4 w-4"/></ToolBtn>
        <ToolBtn onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()} title="Ripristina" testid="editor-redo"><Redo2 className="h-4 w-4"/></ToolBtn>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
