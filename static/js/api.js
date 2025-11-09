/**
 * Classe para gerenciar as chamadas à API
 */
class API {
  /**
   * Realiza uma requisição HTTP
   * @param {string} url - URL da requisição
   * @param {string} method - Método HTTP (GET, POST, PUT, DELETE)
   * @param {object} data - Dados a serem enviados (para POST, PUT)
   * @returns {Promise} - Promise com a resposta da requisição
   */
  static async request(url, method = "GET", data = null) {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    }

    if (data) {
      options.body = JSON.stringify(data)
    }

    try {
      const response = await fetch(url, options)
      const responseData = await response.json()

      if (!response.ok) {
        throw new Error(responseData.erro || "Ocorreu um erro na requisição")
      }

      return responseData
    } catch (error) {
      console.error("Erro na requisição:", error)
      throw error
    }
  }

  /**
   * Realiza login de usuário
   * @param {string} username - Nome de usuário
   * @param {string} password - Senha
   * @returns {Promise} - Promise com os dados do usuário logado
   */
  static async login(username, password) {
    return this.request("/usuario/login", "POST", { username, password })
  }

  /**
   * Cadastra um novo usuário
   * @param {object} userData - Dados do usuário
   * @returns {Promise} - Promise com a resposta do cadastro
   */
  static async cadastrarUsuario(userData) {
    return this.request("/usuario", "POST", userData)
  }

  /**
   * Lista todos os usuários
   * @returns {Promise} - Promise com a lista de usuários
   */
  static async listarUsuarios() {
    return this.request("/usuario")
  }

  /**
   * Obtém um usuário pelo ID
   * @param {number} id - ID do usuário
   * @returns {Promise} - Promise com os dados do usuário
   */
  static async obterUsuarioPorId(id) {
    return this.request(`/usuario/${id}`)
  }

  /**
   * Exclui um usuário pelo ID
   * @param {number} id - ID do usuário
   * @returns {Promise} - Promise com a resposta da exclusão
   */
  static async excluirUsuario(id) {
    return this.request(`/usuario/${id}`, "DELETE")
  }
}
