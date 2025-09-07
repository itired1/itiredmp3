let currentTab = "dashboard";
let currentTrack = null;
let isPlaying = false;
let audioPlayer = null;
let currentPlaylist = [];
let currentTrackIndex = 0;
let isShuffle = false;
let isRepeat = false;
let currentService = "yandex";

document.addEventListener("DOMContentLoaded", function () {
  initApp();
  setupEventListeners();
  initAudioPlayer();
  applySavedTheme();
  loadServiceSetting();
});

function initApp() {
  checkAuth();
  loadProfile();
  loadDashboard();
}

function applySavedTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.body.setAttribute("data-theme", savedTheme);
}

function loadServiceSetting() {
  apiCall("settings")
    .then((settings) => {
      if (settings && settings.music_service) {
        currentService = settings.music_service;
        updateServiceUI();
      }
    })
    .catch(console.error);
}

function updateServiceUI() {
  const serviceSelect = document.getElementById("musicService");
  if (serviceSelect) {
    serviceSelect.value = currentService;
  }

  const serviceIcon = document.getElementById("currentServiceIcon");
  if (serviceIcon) {
    serviceIcon.className =
      currentService === "yandex" ? "fab fa-yandex" : "fab fa-vk";
    serviceIcon.title =
      currentService === "yandex" ? "Яндекс.Музыка" : "VK Музыка";
  }
}

function initAudioPlayer() {
  audioPlayer = document.getElementById("audioPlayer");
  if (!audioPlayer) {
    audioPlayer = document.createElement("audio");
    audioPlayer.id = "audioPlayer";
    audioPlayer.hidden = true;
    document.body.appendChild(audioPlayer);
  }

  audioPlayer.addEventListener("timeupdate", updateProgress);
  audioPlayer.addEventListener("ended", handleTrackEnd);
  audioPlayer.addEventListener("pause", updatePlayButton);
  audioPlayer.addEventListener("play", updatePlayButton);
  audioPlayer.addEventListener("error", function (e) {
    console.error("Audio error:", e);
    showNotification("Ошибка воспроизведения", "error");
  });
}
function openSettingsModal() {
  const modalContent = `
        <div class="modal-content settings-modal">
            <div class="settings-header">
                <h3>Настройки</h3>
                <button class="modal-close" onclick="closeModal('settingsModal')">×</button>
            </div>
            <div class="settings-body">
                <div class="setting-group">
                    <label for="themeSelect">Тема:</label>
                    <select id="themeSelect">
                        <option value="dark">Темная</option>
                        <option value="light">Светлая</option>
                        <option value="blue">Синяя</option>
                        <option value="green">Зеленая</option>
                        <option value="auto">Авто</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label for="languageSelect">Язык:</label>
                    <select id="languageSelect">
                        <option value="ru">Русский</option>
                        <option value="en">English</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label for="musicService">Музыкальный сервис:</label>
                    <select id="musicService">
                        <option value="yandex">Яндекс.Музыка</option>
                        <option value="vk">VK Музыка</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label class="toggle-container">
                        <span>Автовоспроизведение</span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="autoPlayToggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </label>
                </div>
                
                <div class="setting-group">
                    <label class="toggle-container">
                        <span>Показывать эксплицитный контент</span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="explicitToggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </label>
                </div>
            </div>
            <div class="settings-footer">
                <button class="btn-secondary" onclick="closeModal('settingsModal')">Отмена</button>
                <button class="btn-primary" onclick="saveSettings()">Сохранить</button>
            </div>
        </div>
    `;

  showCustomModal(modalContent, "settingsModal");
  loadSettings(); // Загружаем текущие настройки
}

function openThemesModal() {
  const modalContent = `
        <div class="modal-content themes-modal">
            <div class="themes-header">
                <h3>Кастомные темы</h3>
                <button class="modal-close" onclick="closeModal('themesModal')">×</button>
            </div>
            <div class="themes-grid" id="themesContainer">
                <div class="loading">Загрузка тем...</div>
            </div>
            <div class="settings-footer">
                <button class="btn-primary" onclick="showThemeCreator()">
                    <i class="fas fa-plus"></i> Создать тему
                </button>
            </div>
        </div>
    `;

  showCustomModal(modalContent, "themesModal");
  loadThemes();
}

function showCustomModal(content, modalId = "customModal") {
  let modal = document.getElementById(modalId);
  if (!modal) {
    modal = document.createElement("div");
    modal.id = modalId;
    modal.className = "modal";
    modal.onclick = function (e) {
      if (e.target === modal) closeModal(modalId);
    };
    document.body.appendChild(modal);
  }

  modal.innerHTML = content;
  modal.style.display = "block";
  document.body.style.overflow = "hidden";
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "";
  }
}

// Функция для загрузки настроек в форму
async function loadSettings() {
  try {
    const settings = await apiCall("settings");
    if (settings) {
      document.getElementById("themeSelect").value = settings.theme || "dark";
      document.getElementById("languageSelect").value =
        settings.language || "ru";
      document.getElementById("musicService").value =
        settings.music_service || "yandex";
      document.getElementById("autoPlayToggle").checked =
        settings.auto_play !== false;
      document.getElementById("explicitToggle").checked =
        settings.show_explicit !== false;
    }
  } catch (error) {
    console.error("Error loading settings:", error);
  }
}
function setupEventListeners() {
  document.querySelectorAll(".nav-item[data-tab]").forEach(function (item) {
    item.addEventListener("click", function (e) {
      e.preventDefault();
      const tab = this.dataset.tab;
      if (tab) {
        switchTab(tab);
      }
    });
  });

  const globalSearch = document.getElementById("globalSearch");
  if (globalSearch) {
    globalSearch.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        globalSearch();
      }
    });
  }

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        performSearch();
      }
    });
  }

  document.addEventListener("click", function (e) {
    const trackElement = e.target.closest(".track-item");
    if (trackElement) {
      const trackId = trackElement.dataset.trackId;
      if (trackId) {
        playTrack(trackId);
      }
    }
  });

  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("modal")) {
      closeModal(e.target.id);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal").forEach((modal) => {
        if (modal.style.display === "block") {
          closeModal(modal.id);
        }
      });
    }
  });

  const settingsForm = document.getElementById("settingsForm");
  if (settingsForm) {
    settingsForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      await saveSettings();
    });
  }

  const volumeSlider = document.getElementById("volumeSlider");
  if (volumeSlider) {
    volumeSlider.addEventListener("input", function () {
      changeVolume(this.value);
    });
  }

  const serviceSelect = document.getElementById("musicService");
  if (serviceSelect) {
    serviceSelect.addEventListener("change", function () {
      currentService = this.value;
      saveServiceSetting();
      showNotification(
        `Сервис изменен на: ${
          this.value === "yandex" ? "Яндекс.Музыка" : "VK Музыка"
        }`,
        "success"
      );
      loadDashboard();
    });
  }
}
// Управление кастомными темами
async function loadThemesModal() {
  try {
    const response = await apiCall("themes");
    const themesContainer = document.getElementById("themesContainer");

    if (response && themesContainer) {
      let html = `
                <div class="themes-header">
                    <h4>Мои темы</h4>
                    <button class="btn-primary" onclick="showThemeCreator()">
                        <i class="fas fa-plus"></i> Новая тема
                    </button>
                </div>
                <div class="themes-grid">
            `;

      if (response.customThemes && response.customThemes.length > 0) {
        response.customThemes.forEach((theme) => {
          html += `
                        <div class="theme-card" style="background: ${
                          theme.colors.bgPrimary || "#1a1a1a"
                        }; color: ${theme.colors.textPrimary || "#ffffff"}">
                            <div class="theme-preview" style="background: ${
                              theme.colors.bgSecondary || "#2a2a2a"
                            }">
                                ${
                                  theme.background_url
                                    ? `<img src="${theme.background_url}" alt="${theme.name}">`
                                    : `<div class="theme-colors">
                                        <span style="background: ${
                                          theme.colors.accent || "#ff6b6b"
                                        }"></span>
                                        <span style="background: ${
                                          theme.colors.success || "#4ecdc4"
                                        }"></span>
                                        <span style="background: ${
                                          theme.colors.warning || "#ffe66d"
                                        }"></span>
                                    </div>`
                                }
                            </div>
                            <div class="theme-info">
                                <h5>${theme.name}</h5>
                                <div class="theme-actions">
                                    <button onclick="applyTheme('${
                                      theme.name
                                    }')">Применить</button>
                                    <button onclick="deleteTheme(${
                                      theme.id
                                    })">Удалить</button>
                                </div>
                            </div>
                        </div>
                    `;
        });
      } else {
        html += "<p>Нет созданных тем</p>";
      }

      html += "</div>";
      themesContainer.innerHTML = html;
    }
  } catch (error) {
    console.error("Error loading themes:", error);
  }
}

function showThemeCreator() {
  closeModal("themesModal");
  openModal("themeCreatorModal");
}

document
  .getElementById("themeCreatorForm")
  ?.addEventListener("submit", async function (e) {
    e.preventDefault();

    const themeData = {
      name: document.getElementById("themeName").value,
      colors: {
        bgPrimary: document.getElementById("bgPrimary").value,
        bgSecondary: document.getElementById("bgSecondary").value,
        textPrimary: document.getElementById("textPrimary").value,
        textSecondary: document.getElementById("textSecondary").value,
        accent: document.getElementById("accent").value,
        success: document.getElementById("success").value,
      },
      background_url: document.getElementById("themeBackground").value || null,
    };

    await saveCustomTheme(themeData);
  });

async function saveCustomTheme(themeData) {
  try {
    const response = await apiCall("themes", {
      method: "POST",
      body: JSON.stringify({
        action: "save_custom",
        theme: themeData,
      }),
    });

    if (response.success) {
      showNotification("Тема сохранена", "success");
      closeModal("themeCreatorModal");
      await loadThemes();
    }
  } catch (error) {
    showNotification("Ошибка сохранения темы", "error");
  }
}

async function deleteTheme(themeId) {
  if (confirm("Удалить эту тему?")) {
    try {
      const response = await apiCall(`themes?id=${themeId}`, {
        method: "DELETE",
      });

      if (response.success) {
        showNotification("Тема удалена", "success");
        await loadThemes();
      }
    } catch (error) {
      showNotification("Ошибка удаления темы", "error");
    }
  }
}

// Горячие клавиши
document.addEventListener("keydown", function (e) {
  // Пропускаем если ввод в текстовом поле
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

  // Space - play/pause
  if (e.code === "Space") {
    e.preventDefault();
    togglePlay();
  }
  // Right Arrow - next track
  else if (e.code === "ArrowRight") {
    e.preventDefault();
    playNext();
  }
  // Left Arrow - previous track
  else if (e.code === "ArrowLeft") {
    e.preventDefault();
    playPrevious();
  }
  // M - mute/unmute
  else if (e.code === "KeyM") {
    e.preventDefault();
    toggleMute();
  }
});

function toggleMute() {
  audioPlayer.muted = !audioPlayer.muted;
  showNotification(
    audioPlayer.muted ? "Звук выключен" : "Звук включен",
    "info"
  );
}

// Инициализация перетаскивания
function initializeDragAndDrop() {
  const draggableElements = document.querySelectorAll(
    ".desktop-widget, .modal-content"
  );

  draggableElements.forEach((element) => {
    element.addEventListener("mousedown", startDrag);
  });
}

function startDrag(e) {
  // Реализация перетаскивания
  // ... (код из предыдущего ответа)
}

// Автосохранение каждые 30 секунд
setInterval(() => {
  if (playbackQueue.length > 0) {
    saveQueue();
  }
}, 30000);

// Восстановление при загрузке страницы
window.addEventListener("beforeunload", () => {
  if (playbackQueue.length > 0) {
    localStorage.setItem(
      "lastQueue",
      JSON.stringify({
        queue: playbackQueue,
        index: currentQueueIndex,
      })
    );
  }
});
async function saveServiceSetting() {
  try {
    await apiCall("settings", {
      method: "POST",
      body: JSON.stringify({ music_service: currentService }),
    });
    updateServiceUI();
  } catch (error) {
    console.error("Error saving service setting:", error);
  }
}

async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch("/api/" + endpoint, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include",
      ...options,
    });

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error("API call failed:", error);
    throw error;
  }
}

async function checkAuth() {
  try {
    const response = await fetch("/api/profile");
    if (response.status === 401) {
      window.location.href = "/login";
    }
  } catch (error) {
    console.error("Auth check failed:", error);
    window.location.href = "/login";
  }
}

async function checkYandexToken() {
  try {
    const response = await apiCall("check_yandex_token");
    return response;
  } catch (error) {
    return { valid: false, message: "Ошибка проверки токена" };
  }
}

async function checkVkToken() {
  try {
    const response = await apiCall("check_vk_token");
    return response;
  } catch (error) {
    return { valid: false, message: "Ошибка проверки токена" };
  }
}

async function loadProfile() {
  try {
    const profile = await apiCall("profile");
    updateProfileUI(profile);
    updateHeaderProfile(profile);
  } catch (error) {
    console.error("Error loading profile:", error);
  }
}

function updateProfileUI(profile) {
  if (profile && profile.local) {
    const userName = document.getElementById("userName");
    const sidebarUsername = document.getElementById("sidebarUsername");
    const userAvatar = document.getElementById("userAvatar");

    if (userName)
      userName.textContent =
        profile.local.display_name || profile.local.username;
    if (sidebarUsername) sidebarUsername.textContent = profile.local.username;

    if (userAvatar) {
      if (profile.local.avatar_url) {
        userAvatar.innerHTML =
          '<img src="' +
          profile.local.avatar_url +
          '" alt="' +
          (profile.local.display_name || profile.local.username) +
          '" style="width:100%;height:100%;border-radius:50%;object-fit:cover">';
      } else {
        userAvatar.innerHTML = '<i class="fas fa-user"></i>';
      }
    }
  }
}

function updateHeaderProfile(profile) {
  if (profile && profile.local) {
    const headerUsername = document.getElementById("headerUsername");
    const headerUserAvatar = document.getElementById("headerUserAvatar");

    if (headerUsername) headerUsername.textContent = profile.local.username;

    if (headerUserAvatar) {
      if (profile.local.avatar_url) {
        headerUserAvatar.innerHTML =
          '<img src="' +
          profile.local.avatar_url +
          '" alt="' +
          (profile.local.display_name || profile.local.username) +
          '" style="width:100%;height:100%;border-radius:50%;object-fit:cover">';
      } else {
        headerUserAvatar.innerHTML = '<i class="fas fa-user"></i>';
      }
    }
  }
}

async function loadDashboard() {
  try {
    let tokenStatus;
    if (currentService === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      displayRecommendations([]);
      displayRecentTracks([]);
      updateWelcomeStats({ total_liked_tracks: 0, total_playlists: 0 });
      return;
    }

    const [recommendations, likedTracks, stats, listeningHistory] =
      await Promise.all([
        apiCall("recommendations").catch(() => []),
        apiCall("liked_tracks").catch(() => []),
        apiCall("stats").catch(() => ({})),
        apiCall("listening_history").catch(() => []),
      ]);

    displayRecommendations(recommendations);
    displayRecentTracks(listeningHistory);
    updateWelcomeStats(stats);
  } catch (error) {
    console.error("Error loading dashboard:", error);
  }
}

function updateWelcomeStats(stats) {
  const welcomeTracks = document.getElementById("welcomeTracks");
  const welcomePlaylists = document.getElementById("welcomePlaylists");

  if (welcomeTracks) welcomeTracks.textContent = stats.total_liked_tracks || 0;
  if (welcomePlaylists)
    welcomePlaylists.textContent = stats.total_playlists || 0;
}

function displayRecommendations(recommendations) {
  const grid = document.getElementById("recommendationsGrid");
  if (!grid) return;

  if (!recommendations || recommendations.length === 0) {
    grid.innerHTML =
      '<div class="error">Нет рекомендаций. Настройте токен музыки.</div>';
    return;
  }

  let html = "";
  recommendations.forEach(function (item) {
    html +=
      '<div class="playlist-card" onclick="showItem(\'' +
      item.id +
      "', '" +
      item.type +
      "')\">";
    if (item.cover_uri) {
      html +=
        '<img src="' +
        item.cover_uri +
        '" alt="' +
        item.title +
        '" class="playlist-cover">';
    } else {
      html +=
        '<div class="playlist-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
      html += '<i class="fas fa-music" style="font-size:3em;color:#666"></i>';
      html += "</div>";
    }
    html += "<h4>" + item.title + "</h4>";
    if (item.type === "track") {
      html += "<p>" + (item.artists ? item.artists.join(", ") : "") + "</p>";
    } else {
      html += "<p>" + (item.track_count || 0) + " треков</p>";
    }
    html +=
      '<span class="service-badge ' +
      item.service +
      '">' +
      (item.service === "yandex" ? "Y" : "VK") +
      "</span>";
    html += "</div>";
  });

  grid.innerHTML = html;
}

function displayRecentTracks(tracks) {
  const container = document.getElementById("recentTracks");
  if (!container) return;

  if (!tracks || tracks.length === 0) {
    container.innerHTML = '<div class="error">Нет недавних треков</div>';
    return;
  }

  let html = "";
  tracks.forEach(function (track) {
    html += '<div class="track-item" data-track-id="' + track.id + '">';
    if (track.cover_uri) {
      html +=
        '<img src="' +
        track.cover_uri +
        '" alt="' +
        track.title +
        '" class="track-cover">';
    } else {
      html +=
        '<div class="track-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
      html += '<i class="fas fa-music" style="color:#666"></i>';
      html += "</div>";
    }
    html += '<div class="track-info">';
    html += "<h4>" + track.title + "</h4>";
    html +=
      "<p>" +
      (track.artists ? track.artists.join(", ") : "") +
      " • " +
      (track.album || "") +
      "</p>";
    html += "</div>";
    html +=
      '<span class="track-duration">' +
      formatDuration(track.duration) +
      "</span>";
    html +=
      '<span class="service-badge ' +
      track.service +
      '">' +
      (track.service === "yandex" ? "Y" : "VK") +
      "</span>";
    html += "</div>";
  });

  container.innerHTML = html;
}

async function loadPlaylists() {
  try {
    let tokenStatus;
    if (currentService === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      const grid = document.getElementById("playlistsGrid");
      if (grid) {
        grid.innerHTML = '<div class="error">Настройте токен музыки</div>';
      }
      return;
    }

    const playlists = await apiCall("playlists");
    const playlistsCount = document.getElementById("playlistsCount");
    const grid = document.getElementById("playlistsGrid");

    if (playlistsCount)
      playlistsCount.textContent = playlists.length + " плейлистов";

    if (grid) {
      if (!playlists || playlists.length === 0) {
        grid.innerHTML = '<div class="error">Нет плейлистов</div>';
        return;
      }

      let html = "";
      playlists.forEach(function (playlist) {
        html +=
          '<div class="playlist-card" onclick="showPlaylist(\'' +
          playlist.id +
          "')\">";
        if (playlist.cover_uri) {
          html +=
            '<img src="' +
            playlist.cover_uri +
            '" alt="' +
            playlist.title +
            '" class="playlist-cover">';
        } else {
          html +=
            '<div class="playlist-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
          html +=
            '<i class="fas fa-music" style="font-size:3em;color:#666"></i>';
          html += "</div>";
        }
        html += "<h4>" + playlist.title + "</h4>";
        html += "<p>" + playlist.track_count + " треков</p>";
        if (playlist.description) {
          html +=
            '<p style="font-size:0.8em;margin-top:5px">' +
            playlist.description +
            "</p>";
        }
        html +=
          '<span class="service-badge ' +
          playlist.service +
          '">' +
          (playlist.service === "yandex" ? "Y" : "VK") +
          "</span>";
        html += "</div>";
      });

      grid.innerHTML = html;
    }
  } catch (error) {
    const grid = document.getElementById("playlistsGrid");
    if (grid) {
      grid.innerHTML = '<div class="error">Ошибка загрузки плейлистов</div>';
    }
  }
}

async function loadLikedTracks() {
  try {
    let tokenStatus;
    if (currentService === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      const container = document.getElementById("likedTracks");
      if (container) {
        container.innerHTML = '<div class="error">Настройте токен музыки</div>';
      }
      return;
    }

    const tracks = await apiCall("liked_tracks");
    currentPlaylist = tracks;

    const likedCount = document.getElementById("likedCount");
    const container = document.getElementById("likedTracks");

    if (likedCount) likedCount.textContent = tracks.length + " треков";

    if (container) {
      if (!tracks || tracks.length === 0) {
        container.innerHTML = '<div class="error">Нет лайкнутых треков</div>';
        return;
      }

      let html = "";
      tracks.forEach(function (track, index) {
        html += '<div class="track-item" data-track-id="' + track.id + '">';
        if (track.cover_uri) {
          html +=
            '<img src="' +
            track.cover_uri +
            '" alt="' +
            track.title +
            '" class="track-cover">';
        } else {
          html +=
            '<div class="track-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
          html += '<i class="fas fa-music" style="color:#666"></i>';
          html += "</div>";
        }
        html += '<div class="track-info">';
        html += "<h4>" + track.title + "</h4>";
        html +=
          "<p>" +
          (track.artists ? track.artists.join(", ") : "") +
          " • " +
          (track.album || "") +
          " • " +
          (track.year || "") +
          "</p>";
        html += "</div>";
        html +=
          '<span class="track-duration">' +
          formatDuration(track.duration) +
          "</span>";
        html +=
          '<span class="service-badge ' +
          track.service +
          '">' +
          (track.service === "yandex" ? "Y" : "VK") +
          "</span>";
        html += "</div>";
      });

      container.innerHTML = html;
    }
  } catch (error) {
    const container = document.getElementById("likedTracks");
    if (container) {
      container.innerHTML =
        '<div class="error">Ошибка загрузки лайкнутых треков</div>';
    }
  }
}

async function loadStats() {
  try {
    let tokenStatus;
    if (currentService === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      const statsGrid = document.getElementById("statsGrid");
      if (statsGrid) {
        statsGrid.innerHTML = '<div class="error">Настройте токен музыки</div>';
      }
      return;
    }

    const stats = await apiCall("stats");
    const statsGrid = document.getElementById("statsGrid");
    const genreChart = document.getElementById("genreChart");

    if (statsGrid) {
      let html = "";

      if (stats.total_playlists !== undefined) {
        html += '<div class="stat-card">';
        html += '<div class="stat-icon"><i class="fas fa-list"></i></div>';
        html += '<div class="stat-info">';
        html += '<div class="stat-number">' + stats.total_playlists + "</div>";
        html += '<div class="stat-label">Плейлистов</div>';
        html += "</div></div>";
      }

      if (stats.total_liked_tracks !== undefined) {
        html += '<div class="stat-card">';
        html += '<div class="stat-icon"><i class="fas fa-heart"></i></div>';
        html += '<div class="stat-info">';
        html +=
          '<div class="stat-number">' + stats.total_liked_tracks + "</div>";
        html += '<div class="stat-label">Лайкнутых треков</div>';
        html += "</div></div>";
      }

      if (stats.total_artists !== undefined) {
        html += '<div class="stat-card">';
        html += '<div class="stat-icon"><i class="fas fa-users"></i></div>';
        html += '<div class="stat-info">';
        html += '<div class="stat-number">' + stats.total_artists + "</div>";
        html += '<div class="stat-label">Артистов</div>';
        html += "</div></div>";
      }

      if (stats.largest_playlist !== undefined) {
        html += '<div class="stat-card">';
        html += '<div class="stat-icon"><i class="fas fa-music"></i></div>';
        html += '<div class="stat-info">';
        html += '<div class="stat-number">' + stats.largest_playlist + "</div>";
        html += '<div class="stat-label">Самый большой плейлист</div>';
        html += "</div></div>";
      }

      statsGrid.innerHTML = html || '<div class="error">Нет статистики</div>';
    }

    if (genreChart && stats.genre_stats) {
      let genreHtml = "";
      Object.entries(stats.genre_stats).forEach(function ([genre, count]) {
        const percentage = (count / stats.total_liked_tracks) * 100;
        genreHtml += '<div style="margin-bottom:15px">';
        genreHtml +=
          '<div style="display:flex;justify-content:space-between;margin-bottom:5px">';
        genreHtml += "<span>" + genre + "</span>";
        genreHtml +=
          "<span>" + count + " (" + percentage.toFixed(1) + "%)</span>";
        genreHtml += "</div>";
        genreHtml +=
          '<div style="background:#333;height:8px;border-radius:4px;overflow:hidden">';
        genreHtml +=
          '<div style="background:var(--accent);height:100%;width:' +
          percentage +
          '%"></div>';
        genreHtml += "</div>";
        genreHtml += "</div>";
      });
      genreChart.innerHTML = genreHtml;
    }
  } catch (error) {
    const statsGrid = document.getElementById("statsGrid");
    if (statsGrid) {
      statsGrid.innerHTML =
        '<div class="error">Ошибка загрузки статистики</div>';
    }
  }
}

async function performSearch() {
  const searchInput = document.getElementById("searchInput");
  if (!searchInput) return;

  const query = searchInput.value.trim();
  if (!query) return;

  try {
    let tokenStatus;
    if (currentService === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      showNotification("Настройте токен музыки для поиска", "warning");
      return;
    }

    const results = await apiCall("search?q=" + encodeURIComponent(query));
    displaySearchResults(results);
  } catch (error) {
    const searchResults = document.getElementById("searchResults");
    if (searchResults) {
      searchResults.innerHTML = '<div class="error">Ошибка поиска</div>';
    }
  }
}

function displaySearchResults(results) {
  const container = document.getElementById("searchResults");
  if (!container) return;

  let html = "";

  if (results.tracks && results.tracks.length > 0) {
    html += "<h3>Треки</h3>";
    results.tracks.forEach(function (track) {
      html += '<div class="track-item" data-track-id="' + track.id + '">';
      if (track.cover_uri) {
        html +=
          '<img src="' +
          track.cover_uri +
          '" alt="' +
          track.title +
          '" class="track-cover">';
      } else {
        html +=
          '<div class="track-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
        html += '<i class="fas fa-music" style="color:#666"></i>';
        html += "</div>";
      }
      html += '<div class="track-info">';
      html += "<h4>" + track.title + "</h4>";
      html +=
        "<p>" +
        (track.artists ? track.artists.join(", ") : "") +
        " • " +
        (track.album || "") +
        "</p>";
      html += "</div>";
      html +=
        '<span class="track-duration">' +
        formatDuration(track.duration) +
        "</span>";
      html +=
        '<span class="service-badge ' +
        track.service +
        '">' +
        (track.service === "yandex" ? "Y" : "VK") +
        "</span>";
      html += "</div>";
    });
  }

  if (results.albums && results.albums.length > 0) {
    html += '<h3 style="margin-top:30px">Альбомы</h3>';
    html += '<div class="grid">';
    results.albums.forEach(function (album) {
      html += '<div class="playlist-card">';
      if (album.cover_uri) {
        html +=
          '<img src="' +
          album.cover_uri +
          '" alt="' +
          album.title +
          '" class="playlist-cover">';
      } else {
        html +=
          '<div class="playlist-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
        html += '<i class="fas fa-album" style="font-size:3em;color:#666"></i>';
        html += "</div>";
      }
      html += "<h4>" + album.title + "</h4>";
      html +=
        "<p>" +
        (album.artists ? album.artists.join(", ") : "") +
        " • " +
        (album.year || "") +
        "</p>";
      html += "<p>" + (album.track_count || 0) + " треков</p>";
      html +=
        '<span class="service-badge ' +
        album.service +
        '">' +
        (album.service === "yandex" ? "Y" : "VK") +
        "</span>";
      html += "</div>";
    });
    html += "</div>";
  }

  if (results.artists && results.artists.length > 0) {
    html += '<h3 style="margin-top:30px">Артисты</h3>';
    html += '<div class="grid">';
    results.artists.forEach(function (artist) {
      html += '<div class="playlist-card">';
      html +=
        '<div class="playlist-cover" style="background:#333;display:flex;align-items:center;justify-content:center">';
      html += '<i class="fas fa-user" style="font-size:3em;color:#666"></i>';
      html += "</div>";
      html += "<h4>" + artist.name + "</h4>";
      html +=
        "<p>" +
        (artist.genres ? artist.genres.join(", ") : "Жанры не указаны") +
        "</p>";
      html +=
        '<span class="service-badge ' +
        artist.service +
        '">' +
        (artist.service === "yandex" ? "Y" : "VK") +
        "</span>";
      html += "</div>";
    });
    html += "</div>";
  }

  if (!html) {
    html = '<div class="error">Ничего не найдено</div>';
  }

  container.innerHTML = html;
}

function globalSearch() {
  const globalSearchInput = document.getElementById("globalSearch");
  const searchInput = document.getElementById("searchInput");

  if (globalSearchInput && searchInput) {
    const query = globalSearchInput.value.trim();
    if (query) {
      switchTab("search");
      searchInput.value = query;
      setTimeout(function () {
        performSearch();
      }, 100);
    }
  }
}

function switchTab(tabName) {
  currentTab = tabName;

  document.querySelectorAll(".nav-item").forEach(function (item) {
    item.classList.remove("active");
    if (item.dataset.tab === tabName) {
      item.classList.add("active");
    }
  });

  document.querySelectorAll(".tab-content").forEach(function (tab) {
    tab.style.display = "none";
    if (tab.id === tabName) {
      tab.style.display = "block";
    }
  });

  if (window.innerWidth <= 1024) {
    document.querySelector(".sidebar").classList.remove("active");
  }

  switch (tabName) {
    case "playlists":
      loadPlaylists();
      break;
    case "liked":
      loadLikedTracks();
      break;
    case "stats":
      loadStats();
      break;
    case "dashboard":
      loadDashboard();
      break;
    case "search":
      const searchInput = document.getElementById("searchInput");
      if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
      }
      const searchResults = document.getElementById("searchResults");
      if (searchResults) {
        searchResults.innerHTML = "";
      }
      break;
  }
}

function toggleSidebar() {
  document.querySelector(".sidebar").classList.toggle("active");
}

async function playTrack(trackId) {
  try {
    let tokenStatus;
    const [service, id] = trackId.split("_");

    if (service === "yandex") {
      tokenStatus = await checkYandexToken();
    } else {
      tokenStatus = await checkVkToken();
    }

    if (!tokenStatus.valid) {
      showNotification("Настройте токен музыки для воспроизведения", "warning");
      return;
    }

    const trackData = await apiCall("play_track/" + service + "_" + id);
    if (trackData.url) {
      audioPlayer.pause();
      audioPlayer.src = trackData.url;
      audioPlayer.load();

      await audioPlayer.play();

      isPlaying = true;
      updatePlayButton();
      updatePlayerUI(trackData);

      currentTrack = trackData;

      if (currentPlaylist.length > 0) {
        currentTrackIndex = currentPlaylist.findIndex(
          (track) => track.id === trackId
        );
      }
    }
  } catch (error) {
    console.error("Error playing track:", error);
    showNotification("Ошибка воспроизведения трека", "error");
  }
}

function updatePlayerUI(trackData) {
  document.getElementById("currentTrack").textContent = trackData.title;
  document.getElementById("currentArtist").textContent =
    trackData.artists.join(", ");
  document.getElementById("totalTime").textContent = formatDuration(
    trackData.duration
  );

  const playerCover = document.getElementById("playerCover");
  if (trackData.cover_uri) {
    playerCover.innerHTML = `<img src="${trackData.cover_uri}" alt="${trackData.title}" 
            style="width:100%;height:100%;border-radius:6px;object-fit:cover">`;
  } else {
    playerCover.innerHTML = '<i class="fas fa-music"></i>';
  }

  playerCover.classList.add("playing");

  // Обновляем иконку сервиса в плеере
  const serviceIcon = document.getElementById("currentServiceIcon");
  if (serviceIcon) {
    serviceIcon.className =
      trackData.service === "yandex" ? "fab fa-yandex" : "fab fa-vk";
    serviceIcon.title =
      trackData.service === "yandex" ? "Яндекс.Музыка" : "VK Музыка";
  }
}

function togglePlay() {
  if (audioPlayer.paused) {
    audioPlayer.play().catch((error) => {
      console.error("Play error:", error);
    });
  } else {
    audioPlayer.pause();
  }
  updatePlayButton();
}

function updatePlayButton() {
  const playIcon = document.getElementById("playIcon");
  if (playIcon) {
    playIcon.className = audioPlayer.paused ? "fas fa-play" : "fas fa-pause";
  }
}

function updateProgress() {
  const progressFill = document.getElementById("progressFill");
  const currentTime = document.getElementById("currentTime");

  if (progressFill && currentTime) {
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressFill.style.width = progress + "%";
    currentTime.textContent = formatDuration(audioPlayer.currentTime * 1000);
  }
}

function handleTrackEnd() {
  if (isRepeat) {
    audioPlayer.currentTime = 0;
    audioPlayer.play();
  } else {
    nextTrack();
  }
}

function seekTrack(event) {
  const progressBar = event.currentTarget;
  const rect = progressBar.getBoundingClientRect();
  const seekPosition = (event.clientX - rect.left) / rect.width;
  audioPlayer.currentTime = audioPlayer.duration * seekPosition;
}

function changeVolume(volume) {
  audioPlayer.volume = volume / 100;
}

function nextTrack() {
  if (currentPlaylist.length > 0) {
    if (isShuffle) {
      currentTrackIndex = Math.floor(Math.random() * currentPlaylist.length);
    } else {
      currentTrackIndex = (currentTrackIndex + 1) % currentPlaylist.length;
    }
    playTrack(currentPlaylist[currentTrackIndex].id);
  }
}

function previousTrack() {
  if (currentPlaylist.length > 0) {
    if (audioPlayer.currentTime > 3) {
      audioPlayer.currentTime = 0;
    } else {
      currentTrackIndex =
        (currentTrackIndex - 1 + currentPlaylist.length) %
        currentPlaylist.length;
      playTrack(currentPlaylist[currentTrackIndex].id);
    }
  }
}

function toggleShuffle() {
  isShuffle = !isShuffle;
  const shuffleBtn = document.querySelector('[onclick="toggleShuffle()"]');
  if (shuffleBtn) {
    shuffleBtn.style.color = isShuffle
      ? "var(--accent)"
      : "var(--text-secondary)";
  }
  showNotification(
    isShuffle ? "Перемешивание включено" : "Перемешивание выключено",
    "info"
  );
}

function toggleRepeat() {
  isRepeat = !isRepeat;
  const repeatBtn = document.querySelector('[onclick="toggleRepeat()"]');
  if (repeatBtn) {
    repeatBtn.style.color = isRepeat
      ? "var(--accent)"
      : "var(--text-secondary)";
  }
  showNotification(isRepeat ? "Повтор включен" : "Повтор выключен", "info");
}

function addToFavorites() {
  if (currentTrack) {
    showNotification("Добавлено в избранное: " + currentTrack.title, "success");
  }
}

function showPlaylist(playlistId) {
  showNotification("Открытие плейлиста: " + playlistId, "info");
}

function showItem(itemId, type) {
  if (type === "track") {
    playTrack(itemId);
  } else {
    showNotification("Открытие: " + type + " " + itemId, "info");
  }
}

function formatDuration(ms) {
  if (!ms) return "0:00";

  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
}

function logout() {
  fetch("/logout")
    .then(function () {
      window.location.href = "/login";
    })
    .catch(function (error) {
      console.error("Logout error:", error);
      window.location.href = "/login";
    });
}

function openModal(modalId) {
  document.getElementById(modalId).style.display = "block";
  document.body.style.overflow = "hidden";

  if (modalId === "settingsModal") {
    loadSettings();
  }
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none";
  document.body.style.overflow = "";
}

async function loadSettings() {
  try {
    const settings = await apiCall("settings");
    if (settings) {
      updateSettingsUI(settings);
    }
  } catch (error) {
    console.error("Error loading settings:", error);
  }
}

function updateSettingsUI(settings) {
  const themeSelect = document.getElementById("themeSelect");
  const languageSelect = document.getElementById("languageSelect");
  const autoPlayToggle = document.getElementById("autoPlayToggle");
  const musicServiceSelect = document.getElementById("musicService");

  if (themeSelect && settings.theme) {
    themeSelect.value = settings.theme;
  }
  if (languageSelect && settings.language) {
    languageSelect.value = settings.language;
  }
  if (autoPlayToggle && settings.auto_play !== undefined) {
    autoPlayToggle.checked = settings.auto_play;
  }
  if (musicServiceSelect && settings.music_service) {
    musicServiceSelect.value = settings.music_service;
    currentService = settings.music_service;
    updateServiceUI();
  }
}

async function saveSettings() {
  try {
    const settings = {
      theme: document.getElementById("themeSelect").value,
      language: document.getElementById("languageSelect").value,
      auto_play: document.getElementById("autoPlayToggle").checked,
      music_service: document.getElementById("musicService").value,
    };

    const response = await apiCall("settings", {
      method: "POST",
      body: JSON.stringify(settings),
    });

    if (response.success) {
      showNotification("Настройки сохранены", "success");
      applyTheme(settings.theme);
      currentService = settings.music_service;
      updateServiceUI();
      closeModal("settingsModal");
    }
  } catch (error) {
    showNotification("Ошибка сохранения настроек", "error");
  }
}

function applyTheme(theme) {
  if (theme === "auto") {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      document.body.setAttribute("data-theme", "dark");
    } else {
      document.body.setAttribute("data-theme", "light");
    }
  } else {
    document.body.setAttribute("data-theme", theme);
  }
  localStorage.setItem("theme", theme);
}

function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        background: ${
          type === "success"
            ? "var(--success)"
            : type === "error"
            ? "var(--danger)"
            : type === "warning"
            ? "var(--warning)"
            : "var(--accent)"
        };
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 3000);
}
