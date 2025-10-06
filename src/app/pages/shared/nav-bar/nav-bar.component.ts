import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked, ChangeDetectorRef } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../../services/auth.service';
import { User } from '../../../models/user.model';
import { NotificationService } from '../../../../services/notification.service';
import { CartService } from '../../../../services/cart.service';
import { ChatbotService } from '../../../../services/chatbot.service';
import { Enterprise, EnterpriseFormData } from '../../../models/enterprise.model';
import { EnterpriseService } from '../../../../services/enterprise.service';

@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    FormsModule
  ],
  templateUrl: './nav-bar.component.html',
  styleUrls: ['./nav-bar.component.css']
})
export class NavBarComponent implements OnInit, AfterViewChecked {
  userType: String = "user";

  user: User | null = null;
  searchTerm: string = '';
  cartItemCount: number = 0;
  sidebar: boolean = false;

  // Lógica dos formulários
  formAtual: 'login' | 'register' | 'forgot' | null = null;
  formTransicao: string = '';

  entFormLayer: number = 0;

  // Dados dos formulários
  email: string = '';
  password: string = '';
  userRegister: User = { username: '', email: '', password: '', role: 'CUSTOMER' };
  enterpriseRegister: EnterpriseFormData  = { nome_fantasia: '', cnpj: '', nome_admin_empresa: '', cpf_adm: '', telefone: ''};
  confirmPassword: string = '';

  // Variáveis do Chatbot
  chat: boolean = false;
  chatStyle: string = 'hidden';
  userMessage: string = '';
  chatMessages: { role: string, parts: { text: string }[] }[] = [];
  isTyping: boolean = false; 

  @ViewChild('chatContent') private chatContent!: ElementRef;

  constructor(
    private authService: AuthService,
    private router: Router,
    private notificationService: NotificationService,
    private cartService: CartService,
    private chatbotService: ChatbotService,
    private enterpriseService: EnterpriseService,
    private cdr: ChangeDetectorRef 
  ) { }

  ngOnInit(): void {
    this.authService.user$.subscribe(user => this.user = user);
    this.cartService.cart$.subscribe(items => {
      this.cartItemCount = items.reduce((total, item) => total + item.quantity, 0);
    });
  }

  hasUpperCase(password: string): boolean {
    return /[A-Z]/.test(password);
  }

  hasLowerCase(password: string): boolean {
    return /[a-z]/.test(password);
  }

  hasNumber(password: string): boolean {
    return /[0-9]/.test(password);
  }

  hasSpecialChar(password: string): boolean {
    return /[!@#$%^&*(),.?":{}|<>]/.test(password);
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  toggleSidebar(): void {
    this.sidebar = !this.sidebar;
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/']);
    this.notificationService.show('Você saiu da sua conta. Volte sempre!', 'info');
  }

  mostrarForm(): boolean {
    return this.formAtual !== null;
  }

  fecharFormulario(): void {
    this.formTransicao = 'saindo-direita';
    setTimeout(() => {
      this.formAtual = null;
    }, 300);
  }

  mudarFormulario(destino: 'login' | 'register' | 'forgot'): void {
    if (this.formAtual === destino) return;

    const isOpening = !this.formAtual;

    if (!isOpening) {
      this.formTransicao = destino === 'login' ? 'saindo-direita' : 'saindo-esquerda';
    }

    setTimeout(() => {
      this.formAtual = destino;
      this.email = '';
      this.password = '';
      this.userRegister = { username: '', email: '', password: '', role: 'CUSTOMER' };
      this.enterpriseRegister = { nome_fantasia: '', cnpj: '', nome_admin_empresa: '', cpf_adm: '', telefone: '' };
      this.confirmPassword = '';
      this.formTransicao = destino === 'login' ? 'entrando-esquerda' : 'entrando-direita';
    }, isOpening ? 0 : 300);
  }

  onSearch(): void {
    if (this.searchTerm.trim()) {
      this.router.navigate(['/search'], { queryParams: { q: this.searchTerm } });
    } else {
      this.router.navigate(['/search']);
    }
  }

  changeEntFormLayer(qntity: number): void {
    if (this.entFormLayer + qntity != -1 && this.entFormLayer + qntity != 3) {
      this.entFormLayer += qntity;
    }
  }

onSubmitLogin(): void {
  if (!this.email || !this.password) {
    this.notificationService.show("Por favor, preencha seu e-mail e senha para entrar.", "warning");
    return;
  }

  const loginObservable = this.userType === 'user'
    ? this.authService.login(this.email, this.password)
    : this.authService.loginEnterprise(this.email, this.password);

  loginObservable.subscribe({
    next: (response) => { // O 'response' do backend contém os dados do usuário

      console.log('Resposta completa do login:', response); 
      console.log('Role do usuário recebida:', response?.user?.role);

      this.notificationService.show('Login realizado com sucesso!', "success");

      if (response.user.role === 'ADMIN') {
        this.router.navigate(['/admin']); // Redireciona para o painel de admin
      } else {
        this.router.navigate(['/']); 
      }
      
      this.fecharFormulario();
    },
    error: (err) => {
      const errorMessage = err.error?.detail || 'E-mail ou senha inválidos.';
      this.notificationService.show(errorMessage, 'error');
    }
  });
}

goToForgotPassword(): void {
    this.router.navigate(['/forgot-password']); // Navega para a página de esqueci a senha
}

onSubmitRegister(): void {
  if (this.userType === 'user') {
    if (!this.userRegister.username || !this.userRegister.email || !this.userRegister.password) {
      this.notificationService.show('Por favor, preencha todos os campos.', 'warning');
      return;
    }
    if (this.userRegister.password !== this.confirmPassword) {
      this.notificationService.show('As senhas não coincidem.', 'error');
      return;
    }

    // --- INÍCIO DA ATUALIZAÇÃO ---
    this.authService.register(this.userRegister).subscribe({
      next: () => {
        // 1. Exibe a nova mensagem, instruindo a verificação do e-mail.
        this.notificationService.show(
          'Cadastro realizado! Verifique seu e-mail para ativar a conta.', 
          'success'
        );
      },
      error: (err) => {
        const errorMessage = err.error?.detail || 'Erro ao cadastrar. Tente novamente.';
        this.notificationService.show(errorMessage, 'error');
      }
    });

  } else { // Lógica para empresa (mantida como está)
    // Lógica para empresa
      const { nome_fantasia, cnpj, nome_admin_empresa, cpf_adm, telefone} = this.enterpriseRegister;
      if (!nome_fantasia || !cnpj || !telefone || !nome_admin_empresa || !cpf_adm) {
        this.notificationService.show('Por favor, preencha todos os campos.', 'warning');
        return;
      }
      this.enterpriseService.registerEnterprise(this.enterpriseRegister).subscribe({
        next: () => {
          this.notificationService.show('Cadastro da empresa enviado para análise!', 'success');
          this.fecharFormulario(); // Fecha o formulário após o envio
        },
        error: (err) => {
          this.notificationService.show(err.error.detail || 'Erro ao cadastrar. Tente novamente.', 'error');
        }
      });
    }
}

  onSubmitForgot(): void {
    if (!this.email) {
      this.notificationService.show("Por favor, insira seu e-mail.", "warning");
      return;
    }
    this.notificationService.show('Instruções enviadas para seu e-mail.', 'info');
    this.fecharFormulario();
  }

  toggleChat(): void {
    this.chat = !this.chat;
    if (this.chat)
      this.chatStyle = 'visible'
    else
      this.chatStyle = 'hidden'
  }

  sendMessage(): void {
    const messageText = this.userMessage.trim();
    if (messageText) {
      this.chatMessages.push({ role: 'user', parts: [{ text: messageText }] });
      this.userMessage = ''; // <-- Limpa o input
      this.isTyping = true; // <-- Ativa a animação
      
      // Força a atualização da view para a barra de rolagem funcionar
      this.cdr.detectChanges(); 
      this.scrollToBottom();

      this.chatbotService.sendMessage(messageText, this.chatMessages).subscribe({
        next: (response) => {
          this.chatMessages.push({ role: 'model', parts: [{ text: response.reply }] });
          this.isTyping = false; // <-- Desativa a animação
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.notificationService.show('Erro ao se comunicar com o chatbot.', 'error');
          this.chatMessages.push({ role: 'model', parts: [{ text: 'Desculpe, ocorreu um erro.' }] });
          this.isTyping = false; // <-- Desativa a animação em caso de erro
          this.cdr.detectChanges();
        }
      });
    }
  }

  private scrollToBottom(): void {
    if (this.chatContent) {
      try {
        this.chatContent.nativeElement.scrollTop = this.chatContent.nativeElement.scrollHeight;
      } catch (err) { }
    }
  }
}
