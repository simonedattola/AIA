import { useState } from "react";
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor,
  useSensor, useSensors,
} from "@dnd-kit/core";
import {
  arrayMove, SortableContext, sortableKeyboardCoordinates,
  useSortable, verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { BLOCK_TYPES_LIBRARY, BLOCK_BY_TYPE, newBlock } from "./registry";
import { EDITORS } from "./BlockEditors";
import {
  GripVertical, ChevronDown, ChevronUp, Trash2, Eye, EyeOff,
  Plus, X, Copy,
} from "lucide-react";

export default function PageBuilder({ blocks, onChange }) {
  const [open, setOpen] = useState(null); // block id currently open
  const [showLibrary, setShowLibrary] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = (e) => {
    const { active, over } = e;
    if (!over || active.id === over.id) return;
    const oldIndex = blocks.findIndex((b) => b.id === active.id);
    const newIndex = blocks.findIndex((b) => b.id === over.id);
    onChange(arrayMove(blocks, oldIndex, newIndex));
  };

  const updateBlock = (id, partial) => {
    onChange(blocks.map((b) => (b.id === id ? { ...b, ...partial } : b)));
  };
  const updateConfig = (id, config) => updateBlock(id, { config });
  const toggleEnabled = (id) => {
    const b = blocks.find((x) => x.id === id);
    updateBlock(id, { enabled: !b.enabled });
  };
  const removeBlock = (id) => {
    if (!window.confirm("Eliminare questa sezione?")) return;
    onChange(blocks.filter((b) => b.id !== id));
    if (open === id) setOpen(null);
  };
  const duplicateBlock = (id) => {
    const b = blocks.find((x) => x.id === id);
    if (!b) return;
    const idx = blocks.findIndex((x) => x.id === id);
    const copy = { ...b, id: crypto.randomUUID(), config: JSON.parse(JSON.stringify(b.config)) };
    const next = [...blocks];
    next.splice(idx + 1, 0, copy);
    onChange(next);
  };
  const addBlock = (type) => {
    const b = newBlock(type);
    onChange([...blocks, b]);
    setShowLibrary(false);
    setOpen(b.id);
  };

  return (
    <div className="space-y-3" data-testid="page-builder">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
          {blocks.map((b) => (
            <SortableBlock
              key={b.id}
              block={b}
              open={open === b.id}
              onToggleOpen={() => setOpen(open === b.id ? null : b.id)}
              onUpdate={(cfg) => updateConfig(b.id, cfg)}
              onToggleEnabled={() => toggleEnabled(b.id)}
              onRemove={() => removeBlock(b.id)}
              onDuplicate={() => duplicateBlock(b.id)}
            />
          ))}
        </SortableContext>
      </DndContext>

      <button
        onClick={() => setShowLibrary(true)}
        className="w-full py-4 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-navy-600 hover:text-navy-600 hover:bg-navy-50 transition-colors font-medium"
        data-testid="page-builder-add-block"
      >
        <Plus className="h-5 w-5 inline mr-2" /> Aggiungi sezione
      </button>

      {showLibrary && (
        <div role="dialog" aria-modal="true" aria-label="Aggiungi sezione" data-testid="block-library-modal" className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[85vh] overflow-y-auto" data-testid="block-library">
            <div className="sticky top-0 bg-white border-b border-slate-200 p-5 flex items-center justify-between">
              <h2 className="font-display text-2xl font-bold text-navy-700">Aggiungi una sezione</h2>
              <button onClick={() => setShowLibrary(false)} data-testid="block-library-close"><X className="h-5 w-5 text-slate-500"/></button>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {BLOCK_TYPES_LIBRARY.map((bt) => {
                const Icon = bt.icon;
                return (
                  <button
                    key={bt.type}
                    onClick={() => addBlock(bt.type)}
                    className="text-left bg-white border-2 border-slate-200 rounded-lg p-5 hover:border-navy-600 hover:bg-navy-50 transition-colors"
                    data-testid={`block-option-${bt.type}`}
                  >
                    <div className="w-11 h-11 rounded-md bg-navy-100 text-navy-700 flex items-center justify-center mb-3"><Icon className="h-5 w-5"/></div>
                    <div className="font-display font-semibold text-navy-700">{bt.label}</div>
                    <div className="text-xs text-slate-500 mt-1">{bt.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SortableBlock({ block, open, onToggleOpen, onUpdate, onToggleEnabled, onRemove, onDuplicate }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: block.id });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.6 : 1 };
  const def = BLOCK_BY_TYPE[block.type];
  const Editor = EDITORS[block.type];
  const Icon = def?.icon;
  return (
    <div ref={setNodeRef} style={style} className={`bg-white rounded-lg border ${block.enabled ? "border-slate-200" : "border-slate-200 opacity-60"} overflow-hidden`} data-testid={`block-row-${block.id}`}>
      <div className="flex items-center gap-2 p-4 border-b border-slate-200">
        <button {...attributes} {...listeners} className="text-slate-400 hover:text-slate-700 cursor-grab active:cursor-grabbing p-1" data-testid="block-drag-handle">
          <GripVertical className="h-5 w-5"/>
        </button>
        {Icon && <div className="w-9 h-9 rounded-md bg-navy-50 text-navy-600 flex items-center justify-center"><Icon className="h-4 w-4"/></div>}
        <div className="flex-1 min-w-0">
          <div className="font-display font-semibold text-navy-700">{def?.label || block.type}</div>
          <div className="text-xs text-slate-500 truncate">{block.config?.title || block.config?.eyebrow || def?.desc}</div>
        </div>
        <button onClick={onToggleEnabled} className="p-2 text-slate-500 hover:bg-slate-100 rounded" title={block.enabled ? "Disabilita" : "Abilita"} data-testid="block-toggle-enabled">
          {block.enabled ? <Eye className="h-4 w-4"/> : <EyeOff className="h-4 w-4"/>}
        </button>
        <button onClick={onDuplicate} className="p-2 text-slate-500 hover:bg-slate-100 rounded" title="Duplica"><Copy className="h-4 w-4"/></button>
        <button onClick={onRemove} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Elimina" data-testid="block-remove"><Trash2 className="h-4 w-4"/></button>
        <button onClick={onToggleOpen} className="p-2 text-navy-600 hover:bg-navy-50 rounded" data-testid="block-toggle-edit">
          {open ? <ChevronUp className="h-4 w-4"/> : <ChevronDown className="h-4 w-4"/>}
        </button>
      </div>
      {open && (
        <div className="p-5 bg-slate-50">
          {Editor ? <Editor config={block.config} onChange={onUpdate} /> : <div className="text-slate-500">Editor non disponibile.</div>}
        </div>
      )}
    </div>
  );
}
