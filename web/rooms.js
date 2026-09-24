/**
 * KYLA room → agent map for penthouse / command-center UI.
 * Ruflo ALWAYS-ON R1/R4. Agent-Reach LIVE R12. Cyber skills R13. R6 stays clip.
 * (online_bridge / live reply wiring lives on feat/online-ops — merge after this stack.)
 */
(function (root) {
  const rooms = [
    { id: 'R1', name: 'HUMANITAS', label: 'Command Center', agent: 'ruflo', status: 'live', suite: 'command' },
    { id: 'R2', name: 'PATIENTIA', label: 'Second Brain', agent: 'stack', status: 'ready', suite: 'memory' },
    { id: 'R3', name: 'TEMPERANTIA', label: 'Trading Room', agent: 'shell', status: 'ready', suite: null },
    { id: 'R4', name: 'INDUSTRIA', label: 'Dev Lab', agent: 'ruflo', status: 'live', suite: 'code' },
    { id: 'R5', name: 'LUXURIA', label: 'Creative Studio', agent: 'stack', status: 'ready', suite: 'write' },
    { id: 'R6', name: 'GULA', label: 'Editing Suite', agent: 'clip', status: 'live', suite: 'video' },
    { id: 'R7', name: 'SUPERBIA', label: 'Broadcast Room', agent: 'stack', status: 'ready', suite: 'video' },
    { id: 'R8', name: 'INVIDIA', label: 'Photo Studio', agent: 'stack', status: 'ready', suite: 'design' },
    { id: 'R9', name: 'CARITAS', label: 'Client Lounge', agent: 'ollama', status: 'ready', suite: null },
    { id: 'R10', name: 'HUMILITAS', label: 'Study Room', agent: 'stack', status: 'ready', suite: 'study' },
    { id: 'R11', name: 'AVARITIA', label: 'Business Ops', agent: 'stack', status: 'ready', suite: 'business' },
    { id: 'R12', name: 'ACEDIA', label: 'Research & Intelligence', agent: 'agent-reach', status: 'live', suite: 'research' },
    { id: 'R13', name: 'IRA', label: 'QA & Security', agent: 'cyber-skills', status: 'live', suite: 'security' },
    { id: 'R14', name: 'CASTITAS', label: 'Life OS', agent: 'shell', status: 'ready', suite: null },
  ];

  const orchestrator = {
    id: 'ruflo',
    aliases: ['ruflo', 'ruflow', 'claude-flow', 'swarm', 'hive'],
    policy: 'always-on',
    liveRooms: ['R1', 'R4', 'R12', 'R13'],
    note: 'Default agent orchestration path. Falls back to stack/ollama only if Node missing.',
  };

  function byId(id) {
    return rooms.find((r) => r.id === id) || null;
  }

  function statusLine(room) {
    if (!room) return 'Unknown room.';
    if (room.agent === 'ruflo') {
      return `Ruflo LIVE · ${room.id} ${room.label} (always-on orchestrator).`;
    }
    if (room.agent === 'clip') {
      return `Clip LIVE · ${room.id} video path (openmontage lazy).`;
    }
    if (room.agent === 'agent-reach') {
      return `Agent-Reach LIVE · ${room.id} research/web (free platforms).`;
    }
    if (room.agent === 'cyber-skills') {
      return `Cyber Skills LIVE · ${room.id} (npx skills pack).`;
    }
    return `${room.agent} · ${room.status} · ${room.label}`;
  }

  root.KYLA_ROOMS = { rooms, orchestrator, byId, statusLine };
})(typeof window !== 'undefined' ? window : globalThis);
