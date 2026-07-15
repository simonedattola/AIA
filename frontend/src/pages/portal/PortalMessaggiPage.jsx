import { useEffect, useRef, useState } from "react";
import {
  portalConversazioni,
  portalConversazione,
  portalInviaMessaggioChat,
  portalAssociatiMessaggi,
  portalCreaGruppo,
  portalUploadAllegatoMessaggio,
  portalModificaMessaggio,
  portalEliminaMessaggio,
  portalReazioneMessaggio,
  portalContattoChat,
  portalInfoGruppo,
  portalAggiornaGruppo,
  portalEliminaConversazione,
} from "../../lib/portal-api";
import "../../styles/whatsapp-chat.css";
import ChatList from "../../components/portal/chat/ChatList";
import ChatWindow from "../../components/portal/chat/ChatWindow";
import MessageContextMenu from "../../components/portal/chat/MessageContextMenu";
import {
  ReadInfoModal,
  GroupInfoDrawer,
  ContactInfoDrawer,
  NewChatModal,
} from "../../components/portal/chat/ChatOverlays";
import { WA } from "../../components/portal/chat/whatsappTheme";

export default function PortalMessaggiPage() {
  const [conversazioni, setConversazioni] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [chat, setChat] = useState(null);
  const [testo, setTesto] = useState("");
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newMode, setNewMode] = useState("chat");
  const [associati, setAssociati] = useState([]);
  const [groupName, setGroupName] = useState("");
  const [groupMembers, setGroupMembers] = useState([]);
  const [mobileShowChat, setMobileShowChat] = useState(false);
  const [error, setError] = useState("");
  const [replyTo, setReplyTo] = useState(null);
  const [editing, setEditing] = useState(null);
  const [menu, setMenu] = useState(null);
  const [showContact, setShowContact] = useState(false);
  const [contact, setContact] = useState(null);
  const [showGroup, setShowGroup] = useState(false);
  const [groupInfo, setGroupInfo] = useState(null);
  const [groupDescDraft, setGroupDescDraft] = useState("");
  const [savingGroup, setSavingGroup] = useState(false);
  const [groupPhotoUrl, setGroupPhotoUrl] = useState("");
  const [groupPhotoPreview, setGroupPhotoPreview] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [readInfo, setReadInfo] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showEmojiBar, setShowEmojiBar] = useState(false);
  const [leavingGroup, setLeavingGroup] = useState(false);
  const [deletingChat, setDeletingChat] = useState(false);
  const bottomRef = useRef(null);
  const fileRef = useRef(null);
  const groupPhotoRef = useRef(null);
  const groupPanelPhotoRef = useRef(null);
  const me = JSON.parse(localStorage.getItem("aia_member") || "{}");

  const loadConversazioni = () => portalConversazioni().then(setConversazioni);

  const refreshChat = async (chatId = activeChatId) => {
    if (!chatId) return;
    const data = await portalConversazione(chatId);
    setChat(data);
    return data;
  };

  useEffect(() => {
    loadConversazioni();
    portalAssociatiMessaggi().then(setAssociati);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages]);

  const openChat = async (chatId) => {
    const data = await portalConversazione(chatId);
    setActiveChatId(chatId);
    setChat(data);
    setMobileShowChat(true);
    setShowNew(false);
    setReplyTo(null);
    setEditing(null);
    setMenu(null);
    loadConversazioni();
  };

  const openInfoPanel = () => {
    if (chat?.isGroup) openGroupPanel();
    else openContactPanel();
  };

  const openContactPanel = async (memberId = null) => {
    const chatId = memberId || activeChatId;
    if (!chatId) return;
    if (!memberId && chat?.isGroup) return;
    try {
      const c = await portalContattoChat(chatId);
      setContact(c);
      setShowContact(true);
    } catch {
      setError("Impossibile caricare il contatto");
    }
  };

  const openMemberFromGroup = async (member) => {
    if (!member?.id || member.id === me.id) return;
    setShowGroup(false);
    await openContactPanel(member.id);
  };

  const esciDalGruppo = async () => {
    const gruppoId = groupInfo?.id || chat?.gruppoId;
    if (!gruppoId) return;
    if (!window.confirm("Eliminare questo gruppo per te? Uscirai dal gruppo e la chat scomparirà dalla tua lista.")) return;
    setLeavingGroup(true);
    setError("");
    try {
      await portalEliminaConversazione(activeChatId);
      setShowGroup(false);
      setGroupInfo(null);
      setActiveChatId(null);
      setChat(null);
      setMobileShowChat(false);
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Impossibile eliminare il gruppo");
    } finally {
      setLeavingGroup(false);
    }
  };

  const eliminaChat = async () => {
    if (!activeChatId || chat?.isGroup) return;
    if (!window.confirm("Eliminare questa chat? Sparirà dalla tua lista. Se ricevi nuovi messaggi, riapparirà.")) return;
    setDeletingChat(true);
    setError("");
    try {
      await portalEliminaConversazione(activeChatId);
      setShowContact(false);
      setContact(null);
      setActiveChatId(null);
      setChat(null);
      setMobileShowChat(false);
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Impossibile eliminare la chat");
    } finally {
      setDeletingChat(false);
    }
  };

  const openGroupPanel = async () => {
    if (!activeChatId || !chat?.isGroup) return;
    try {
      const g = await portalInfoGruppo(activeChatId);
      setGroupInfo(g);
      setGroupDescDraft(g.description || "");
      setShowGroup(true);
    } catch {
      setError("Impossibile caricare le info del gruppo");
    }
  };

  const saveGroupDescription = async () => {
    if (!groupInfo?.id) return;
    setSavingGroup(true);
    try {
      const updated = await portalAggiornaGruppo(groupInfo.id, { description: groupDescDraft });
      setGroupInfo(updated);
      await refreshChat();
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Salvataggio non riuscito");
    } finally {
      setSavingGroup(false);
    }
  };

  const handleGroupPhotoChange = async (e, forCreate = false) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !file.type.startsWith("image/")) {
      setError("Seleziona un'immagine (JPG, PNG, …)");
      return;
    }
    setUploading(true);
    try {
      const up = await portalUploadAllegatoMessaggio(file);
      if (forCreate) {
        setGroupPhotoUrl(up.attachmentUrl);
        setGroupPhotoPreview(up.attachmentUrlResolved || "");
        return;
      }
      if (!groupInfo?.id) return;
      const updated = await portalAggiornaGruppo(groupInfo.id, { photoUrl: up.attachmentUrl });
      setGroupInfo(updated);
      await refreshChat();
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Caricamento foto non riuscito");
    } finally {
      setUploading(false);
    }
  };

  const invia = async (e) => {
    e?.preventDefault();
    if (!activeChatId) return;
    if (editing) {
      if (!testo.trim()) return;
      try {
        await portalModificaMessaggio(editing.id, testo.trim());
        setEditing(null);
        setTesto("");
        await refreshChat();
      } catch (err) {
        setError(err?.response?.data?.detail || "Impossibile modificare il messaggio");
      }
      return;
    }
    if (!testo.trim() && !replyTo) return;
    const payload = { testo: testo.trim() };
    if (replyTo) payload.replyToId = replyTo.id;
    await portalInviaMessaggioChat(activeChatId, payload);
    setTesto("");
    setReplyTo(null);
    await refreshChat();
    loadConversazioni();
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !activeChatId) return;
    setUploading(true);
    setError("");
    try {
      const up = await portalUploadAllegatoMessaggio(file);
      const payload = {
        testo: testo.trim(),
        tipo: up.tipo,
        attachmentUrl: up.attachmentUrl,
        attachmentName: up.attachmentName,
        attachmentMime: up.attachmentMime,
      };
      if (replyTo) payload.replyToId = replyTo.id;
      await portalInviaMessaggioChat(activeChatId, payload);
      setTesto("");
      setReplyTo(null);
      await refreshChat();
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Caricamento allegato fallito");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (m) => {
    if (!window.confirm("Eliminare questo messaggio per tutti?")) return;
    await portalEliminaMessaggio(m.id);
    setMenu(null);
    await refreshChat();
  };

  const handleReaction = async (m, emoji) => {
    await portalReazioneMessaggio(m.id, emoji);
    setMenu(null);
    await refreshChat();
  };

  const filtered = conversazioni.filter((c) =>
    (c.peerName || "").toLowerCase().includes(search.toLowerCase())
  );

  const startNewChat = (peer) => {
    const chatId = peer.id;
    setActiveChatId(chatId);
    setChat({
      chatId,
      type: "direct",
      isGroup: false,
      peerId: peer.id,
      peerName: `${peer.firstName} ${peer.lastName}`.trim() || peer.id,
      peerPhoto: peer.photoUrl || "",
      memberCount: 2,
      messages: [],
    });
    setMobileShowChat(true);
    setShowNew(false);
  };

  const toggleGroupMember = (id) => {
    setGroupMembers((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const creaGruppo = async (e) => {
    e.preventDefault();
    setError("");
    if (!groupName.trim() || groupMembers.length === 0) {
      setError("Nome gruppo e almeno un membro richiesti.");
      return;
    }
    try {
      const res = await portalCreaGruppo({
        name: groupName.trim(),
        memberIds: groupMembers,
        photoUrl: groupPhotoUrl,
        description: groupDescription.trim(),
      });
      setGroupName("");
      setGroupMembers([]);
      setGroupPhotoUrl("");
      setGroupPhotoPreview("");
      setGroupDescription("");
      setShowNew(false);
      await openChat(res.chatId);
      loadConversazioni();
    } catch (err) {
      setError(err?.response?.data?.detail || "Impossibile creare il gruppo");
    }
  };

  const openMenu = (e, m) => {
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    setMenu({ msg: m, x: Math.min(rect.left, window.innerWidth - 200), y: rect.top });
  };

  const canEdit = (m) => m.canEdit === true;

  const listVisible = !mobileShowChat;
  const chatPanelVisible = mobileShowChat;

  return (
    <div
      className="wa-chat-root flex flex-col flex-1 min-h-0 h-full min-h-[480px]"
      style={{ backgroundColor: WA.listBg }}
    >
      <div
        className="wa-chat-shell flex flex-1 min-h-0 overflow-hidden relative"
        style={{ backgroundColor: WA.panelWhite }}
      >
        <ChatList
          search={search}
          onSearchChange={(e) => setSearch(e.target.value)}
          conversazioni={filtered}
          activeChatId={activeChatId}
          onSelectChat={openChat}
          onNewChat={() => {
            setShowNew(true);
            setNewMode("chat");
            setError("");
          }}
          listVisible={listVisible}
        />

        <ChatWindow
          chat={chat}
          me={me}
          panelVisible={chatPanelVisible}
          onBack={() => setMobileShowChat(false)}
          onInfo={openInfoPanel}
          bottomRef={bottomRef}
          error={error}
          onMenu={openMenu}
          onReaction={handleReaction}
          inputProps={{
            testo,
            onTestoChange: (e) => setTesto(e.target.value),
            onSubmit: invia,
            fileRef,
            onFileChange: handleFile,
            uploading,
            editing,
            replyTo,
            onClearReply: () => setReplyTo(null),
            onClearEdit: () => {
              setEditing(null);
              setTesto("");
            },
            showEmojiBar,
            onToggleEmojiBar: () => setShowEmojiBar((v) => !v),
            onEmojiPick: (em) => setTesto((t) => t + em),
          }}
        />
      </div>

      <MessageContextMenu
        menu={menu}
        meId={me.id}
        onClose={() => setMenu(null)}
        onReply={(msg) => {
          setReplyTo(msg);
          setMenu(null);
        }}
        onReaction={handleReaction}
        onEdit={(msg) => {
          setEditing(msg);
          setTesto(msg.testo || "");
          setReplyTo(null);
          setMenu(null);
        }}
        onDelete={handleDelete}
        onInfo={(msg) => {
          setReadInfo(msg);
          setMenu(null);
        }}
        canEdit={canEdit}
      />

      <ReadInfoModal readInfo={readInfo} onClose={() => setReadInfo(null)} />

      <GroupInfoDrawer
        open={showGroup}
        groupInfo={groupInfo}
        groupDescDraft={groupDescDraft}
        onDescChange={(e) => setGroupDescDraft(e.target.value)}
        onSaveDesc={saveGroupDescription}
        savingGroup={savingGroup}
        onClose={() => setShowGroup(false)}
        onPhotoClick={() => groupPanelPhotoRef.current?.click()}
        groupPanelPhotoRef={groupPanelPhotoRef}
        onPhotoChange={(e) => handleGroupPhotoChange(e, false)}
        onMemberClick={openMemberFromGroup}
        onLeaveGroup={esciDalGruppo}
        leavingGroup={leavingGroup}
        meId={me.id}
      />

      <ContactInfoDrawer
        open={showContact}
        contact={contact}
        onClose={() => setShowContact(false)}
        onOpenGroupChat={(chatId) => {
          setShowContact(false);
          openChat(chatId);
        }}
        onDeleteChat={eliminaChat}
        deletingChat={deletingChat}
      />

      <NewChatModal
        open={showNew}
        onClose={() => setShowNew(false)}
        newMode={newMode}
        setNewMode={setNewMode}
        error={error}
        associati={associati}
        onStartChat={startNewChat}
        creaGruppo={creaGruppo}
        groupName={groupName}
        setGroupName={setGroupName}
        groupDescription={groupDescription}
        setGroupDescription={setGroupDescription}
        groupMembers={groupMembers}
        toggleGroupMember={toggleGroupMember}
        groupPhotoPreview={groupPhotoPreview}
        onGroupPhotoClick={() => groupPhotoRef.current?.click()}
        groupPhotoRef={groupPhotoRef}
        onGroupPhotoChange={(e) => handleGroupPhotoChange(e, true)}
      />
    </div>
  );
}
