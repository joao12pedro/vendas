/**
 * Classe para gerenciar os usuários
 */
class UsuariosManager {
  /**
   * Carrega a lista de usuários
   */
  static async carregarUsuarios() {
    try {
      const listaMessage = document.getElementById("lista-message")
      listaMessage.textContent = "Carregando usuários..."
      listaMessage.className = "message"

      const usuarios = await API.listarUsuarios()
      const tbody = document.getElementById("usuarios-body")
      tbody.innerHTML = ""

      if (usuarios && usuarios.length > 0) {
        usuarios.forEach((usuario) => {
          const tr = document.createElement("tr")
          tr.innerHTML = `
                        <td>${usuario.id}</td>
                        <td>${usuario.nome}</td>
                        <td>${usuario.perfil}</td>
                        <td>${usuario.username}</td>
                        <td>
                            <button class="action-btn delete-btn" data-id="${usuario.id}">Excluir</button>
                        </td>
                    `
          tbody.appendChild(tr)
        })

        // Adicionar eventos aos botões de ação
        this.adicionarEventosAcoes()

        listaMessage.textContent = ""
        listaMessage.className = "message hidden"
      } else {
        listaMessage.textContent = "Nenhum usuário encontrado."
        listaMessage.className = "message"
      }
    } catch (error) {
      const listaMessage = document.getElementById("lista-message")
      listaMessage.textContent = `Erro ao carregar usuários: ${error.message}`
      listaMessage.className = "message error"
    }
  }

  /**
   * Adiciona eventos aos botões de ação da tabela
   */
  static adicionarEventosAcoes() {
    // Botões de excluir
    document.querySelectorAll(".delete-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id
        this.confirmarExclusao(id)
      })
    })
  }

  /**
   * Exibe modal de confirmação de exclusão
   * @param {number} id - ID do usuário a ser excluído
   */
  static confirmarExclusao(id) {
    const modal = document.getElementById("confirm-modal")
    const confirmYes = document.getElementById("confirm-yes")
    const confirmNo = document.getElementById("confirm-no")

    modal.classList.remove("hidden")

    // Remover eventos antigos
    const newConfirmYes = confirmYes.cloneNode(true)
    const newConfirmNo = confirmNo.cloneNode(true)

    confirmYes.parentNode.replaceChild(newConfirmYes, confirmYes)
    confirmNo.parentNode.replaceChild(newConfirmNo, confirmNo)

    // Adicionar novos eventos
    newConfirmYes.addEventListener("click", async () => {
      try {
        await API.excluirUsuario(id)
        modal.classList.add("hidden")
        this.carregarUsuarios()

        const listaMessage = document.getElementById("lista-message")
        listaMessage.textContent = "Usuário excluído com sucesso!"
        listaMessage.className = "message success"

        setTimeout(() => {
          listaMessage.className = "message hidden"
        }, 3000)
      } catch (error) {
        const listaMessage = document.getElementById("lista-message")
        listaMessage.textContent = `Erro ao excluir usuário: ${error.message}`
        listaMessage.className = "message error"
        modal.classList.add("hidden")
      }
    })

    newConfirmNo.addEventListener("click", () => {
      modal.classList.add("hidden")
    })
  }

  /**
   * Cadastra um novo usuário
   * @param {object} userData - Dados do usuário
   */
  static async cadastrarUsuario(userData) {
    try {
      const cadastroMessage = document.getElementById("cadastro-message")
      cadastroMessage.textContent = "Cadastrando usuário..."
      cadastroMessage.className = "message"

      await API.cadastrarUsuario(userData)

      cadastroMessage.textContent = "Usuário cadastrado com sucesso!"
      cadastroMessage.className = "message success"

      // Limpar formulário
      document.getElementById("cad-nome").value = ""
      document.getElementById("cad-perfil").value = "aluno"
      document.getElementById("cad-username").value = ""
      document.getElementById("cad-password").value = ""

      setTimeout(() => {
        cadastroMessage.className = "message hidden"
        // Voltar para a lista
        document.getElementById("btn-listar").click()
      }, 2000)
    } catch (error) {
      const cadastroMessage = document.getElementById("cadastro-message")
      cadastroMessage.textContent = `Erro ao cadastrar usuário: ${error.message}`
      cadastroMessage.className = "message error"
    }
  }
}

// Supondo que API esteja definido em outro arquivo, como api.js
// Importe a API ou defina-a aqui. Exemplo:
// import { API } from './api.js';

// Ou, se API for um objeto global já definido:
// const API = window.API;

// Se API precisa ser definido aqui:
const API = {
  listarUsuarios: async () => {
    // Implemente a lógica para listar usuários
    console.warn("API.listarUsuarios() não implementado. Retornando dados mockados.")
    return [
      { id: 1, nome: "Usuário 1", perfil: "admin", username: "user1" },
      { id: 2, nome: "Usuário 2", perfil: "aluno", username: "user2" },
    ]
  },
  excluirUsuario: async (id) => {
    // Implemente a lógica para excluir usuário
    console.warn("API.excluirUsuario() não implementado.")
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`Usuário ${id} excluído (mock).`)
        resolve()
      }, 500)
    })
  },
  cadastrarUsuario: async (userData) => {
    // Implemente a lógica para cadastrar usuário
    console.warn("API.cadastrarUsuario() não implementado.")
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`Usuário ${userData.nome} cadastrado (mock).`)
        resolve()
      }, 500)
    })
  },
}
