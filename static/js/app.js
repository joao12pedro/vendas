document.addEventListener("DOMContentLoaded", () => {
  // Verificar se o usuário está logado
  if (Auth.isLoggedIn()) {
    mostrarAreaPrincipal()
  } else {
    mostrarAreaLogin()
  }

  // Eventos de login e registro
  configurarEventosAutenticacao()

  // Eventos da área principal
  configurarEventosAreaPrincipal()
})

/**
 * Configura os eventos de autenticação (login e registro)
 */
function configurarEventosAutenticacao() {
  // Botão de login
  document.getElementById("login-btn").addEventListener("click", async () => {
    const username = document.getElementById("username").value
    const password = document.getElementById("password").value
    const loginMessage = document.getElementById("login-message")

    if (!username || !password) {
      loginMessage.textContent = "Preencha todos os campos!"
      loginMessage.className = "message error"
      return
    }

    try {
      loginMessage.textContent = "Autenticando..."
      loginMessage.className = "message"

      const response = await API.login(username, password)

      // Salvar usuário no localStorage
      Auth.login(response.usuario)

      loginMessage.textContent = "Login realizado com sucesso!"
      loginMessage.className = "message success"

      setTimeout(() => {
        mostrarAreaPrincipal()
      }, 1000)
    } catch (error) {
      loginMessage.textContent = error.message
      loginMessage.className = "message error"
    }
  })

  // Botão para mostrar área de registro
  document.getElementById("show-register-btn").addEventListener("click", () => {
    document.getElementById("login-area").classList.add("hidden")
    document.getElementById("register-area").classList.remove("hidden")
  })

  // Botão para voltar ao login
  document.getElementById("back-to-login-btn").addEventListener("click", () => {
    document.getElementById("register-area").classList.add("hidden")
    document.getElementById("login-area").classList.remove("hidden")
  })

  // Botão de registro
  document.getElementById("register-btn").addEventListener("click", async () => {
    const nome = document.getElementById("reg-nome").value
    const perfil = document.getElementById("reg-perfil").value
    const username = document.getElementById("reg-username").value
    const password = document.getElementById("reg-password").value
    const registerMessage = document.getElementById("register-message")

    if (!nome || !perfil || !username || !password) {
      registerMessage.textContent = "Preencha todos os campos!"
      registerMessage.className = "message error"
      return
    }

    try {
      registerMessage.textContent = "Cadastrando..."
      registerMessage.className = "message"

      await API.cadastrarUsuario({ nome, perfil, username, password })

      registerMessage.textContent = "Cadastro realizado com sucesso! Redirecionando para o login..."
      registerMessage.className = "message success"

      setTimeout(() => {
        document.getElementById("register-area").classList.add("hidden")
        document.getElementById("login-area").classList.remove("hidden")

        // Preencher campos de login
        document.getElementById("username").value = username
        document.getElementById("password").value = password
      }, 2000)
    } catch (error) {
      registerMessage.textContent = error.message
      registerMessage.className = "message error"
    }
  })
}

/**
 * Configura os eventos da área principal
 */
function configurarEventosAreaPrincipal() {
  // Botão de logout
  document.getElementById("logout-btn").addEventListener("click", () => {
    Auth.logout()
    mostrarAreaLogin()
  })

  // Botão para listar usuários
  document.getElementById("btn-listar").addEventListener("click", () => {
    document.getElementById("lista-usuarios").classList.remove("hidden")
    document.getElementById("form-cadastro").classList.add("hidden")

    document.getElementById("btn-listar").classList.add("active")
    document.getElementById("btn-cadastrar").classList.remove("active")

    UsuariosManager.carregarUsuarios()
  })

  // Botão para mostrar formulário de cadastro
  document.getElementById("btn-cadastrar").addEventListener("click", () => {
    document.getElementById("lista-usuarios").classList.add("hidden")
    document.getElementById("form-cadastro").classList.remove("hidden")

    document.getElementById("btn-listar").classList.remove("active")
    document.getElementById("btn-cadastrar").classList.add("active")
  })

  // Botão para salvar usuário
  document.getElementById("salvar-usuario-btn").addEventListener("click", () => {
    const nome = document.getElementById("cad-nome").value
    const perfil = document.getElementById("cad-perfil").value
    const username = document.getElementById("cad-username").value
    const password = document.getElementById("cad-password").value

    if (!nome || !perfil || !username || !password) {
      const cadastroMessage = document.getElementById("cadastro-message")
      cadastroMessage.textContent = "Preencha todos os campos!"
      cadastroMessage.className = "message error"
      return
    }

    UsuariosManager.cadastrarUsuario({ nome, perfil, username, password })
  })

  // Botão para cancelar cadastro
  document.getElementById("cancelar-cadastro-btn").addEventListener("click", () => {
    document.getElementById("btn-listar").click()
  })
}

/**
 * Mostra a área de login
 */
function mostrarAreaLogin() {
  document.getElementById("login-area").classList.remove("hidden")
  document.getElementById("register-area").classList.add("hidden")
  document.getElementById("main-area").classList.add("hidden")

  // Limpar campos
  document.getElementById("username").value = ""
  document.getElementById("password").value = ""
  document.getElementById("login-message").className = "message hidden"
}

/**
 * Mostra a área principal
 */
function mostrarAreaPrincipal() {
  document.getElementById("login-area").classList.add("hidden")
  document.getElementById("register-area").classList.add("hidden")
  document.getElementById("main-area").classList.remove("hidden")

  // Exibir nome do usuário
  const usuario = Auth.getUsuario()
  document.getElementById("user-display").textContent = `Olá, ${usuario.username}!`

  // Carregar lista de usuários
  document.getElementById("btn-listar").click()
}

const Auth = {
  isLoggedIn: () => {
    return localStorage.getItem("usuario") !== null
  },
  login: (usuario) => {
    localStorage.setItem("usuario", JSON.stringify(usuario))
  },
  logout: () => {
    localStorage.removeItem("usuario")
  },
  getUsuario: () => {
    return JSON.parse(localStorage.getItem("usuario"))
  },
}

const API = {
  login: async (username, password) => {
    // Simulação de login
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (username === "admin" && password === "admin") {
          resolve({ usuario: { username: "admin", nome: "Administrador", perfil: "Administrador" } })
        } else if (username === "user" && password === "user") {
          resolve({ usuario: { username: "user", nome: "Usuário Comum", perfil: "Comum" } })
        } else {
          reject(new Error("Usuário ou senha incorretos."))
        }
      }, 500)
    })
  },
  cadastrarUsuario: async (usuario) => {
    // Simulação de cadastro
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        resolve()
      }, 500)
    })
  },
  listarUsuarios: async () => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const usuarios = [
          { id: 1, nome: "Administrador", perfil: "Administrador", username: "admin" },
          { id: 2, nome: "Usuário Comum", perfil: "Comum", username: "user" },
        ]
        resolve(usuarios)
      }, 500)
    })
  },
}

const UsuariosManager = {
  carregarUsuarios: async () => {
    const listaUsuarios = document.getElementById("lista-usuarios")
    listaUsuarios.innerHTML = ""

    try {
      const usuarios = await API.listarUsuarios()

      if (usuarios.length === 0) {
        listaUsuarios.textContent = "Nenhum usuário cadastrado."
        return
      }

      const tabela = document.createElement("table")
      tabela.className = "usuarios-table"

      const thead = document.createElement("thead")
      const headerRow = document.createElement("tr")
      ;["Nome", "Perfil", "Username"].forEach((headerText) => {
        const th = document.createElement("th")
        th.textContent = headerText
        headerRow.appendChild(th)
      })
      thead.appendChild(headerRow)
      tabela.appendChild(thead)

      const tbody = document.createElement("tbody")
      usuarios.forEach((usuario) => {
        const tr = document.createElement("tr")
        ;["nome", "perfil", "username"].forEach((key) => {
          const td = document.createElement("td")
          td.textContent = usuario[key]
          tr.appendChild(td)
        })
        tbody.appendChild(tr)
      })
      tabela.appendChild(tbody)

      listaUsuarios.appendChild(tabela)
    } catch (error) {
      listaUsuarios.textContent = "Erro ao carregar usuários."
    }
  },
  cadastrarUsuario: async (usuario) => {
    try {
      await API.cadastrarUsuario(usuario)

      const cadastroMessage = document.getElementById("cadastro-message")
      cadastroMessage.textContent = "Usuário cadastrado com sucesso!"
      cadastroMessage.className = "message success"

      setTimeout(() => {
        document.getElementById("btn-listar").click()
      }, 1000)
    } catch (error) {
      const cadastroMessage = document.getElementById("cadastro-message")
      cadastroMessage.textContent = error.message
      cadastroMessage.className = "message error"
    }
  },
}
