import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { EnterpriseFormData } from '../../models/enterprise.model';

import { FooterComponent } from '../shared/footer/footer.component';
import { EnterpriseService } from '../../../services/enterprise.service';
import { NotificationService } from '../../../services/notification.service';
import { UserService } from '../../../services/user.service';
import { AuthService } from '../../../services/auth.service';
import { NgxMaskDirective } from 'ngx-mask';

@Component({
  selector: 'app-gc-guide',
  standalone: true,
  imports: [CommonModule, FormsModule, FooterComponent, NgxMaskDirective],
  templateUrl: './gc-guide.component.html',
  styleUrls: ['./gc-guide.component.css']
})
export class GcGuideComponent implements OnInit{
  enterprise: EnterpriseFormData  = {
    nome_fantasia: '',
    cnpj: '',
    nome_admin_empresa: '',
    cpf_adm: '',
    telefone: ''
  };

  isSubmitting = false; // Variável para controlar o estado do botão

  // Injetar o EnterpriseService em vez do HttpClient
  constructor(
    private enterpriseService: EnterpriseService,
    private router: Router,
    private notificationService: NotificationService,
    private userService: UserService,
    private authService: AuthService
  ) {}

   ngOnInit(): void {
    this.carregarDadosUsuario();
  }

  carregarDadosUsuario(): void {
    this.userService.getMe().subscribe({
      next: (userDetails) => {
        
        // Fluxo 1: Usuário já é um vendedor?
        if (userDetails.role === 'ENTERPRISE' || userDetails.role === 'ADMIN') {
          this.notificationService.show('Você já tem permissão de vendedor.', 'info');
          this.router.navigate(['/dashboard-gc']);
          return;
        }

        // --- INÍCIO DA LÓGICA CORRIGIDA ---
        
        // Fluxo 2: Usuário é Pessoa Física (person)
        if (userDetails.account_type === 'person') {
          this.notificationService.show('Identificamos sua conta PF. Complete seu cadastro para vender.', 'info');
          
          // Autocompletamos os dados de PF
          this.enterprise.nome_admin_empresa = userDetails.username;
          this.enterprise.cpf_adm = userDetails.cpf || '';
          
          // 'cnpj', 'nome_fantasia' e 'telefone' ficam para ele preencher
        }
        
        // Fluxo 3: Usuário é Pessoa Jurídica (enterprise)
        else if (userDetails.account_type === 'enterprise') {
          this.notificationService.show('Identificamos sua conta PJ. Complete seu cadastro para vender.', 'info');
          
          // Autocompletamos os dados de PJ
          this.enterprise.cnpj = userDetails.cnpj || '';
          this.enterprise.nome_admin_empresa = userDetails.username;

          // 'nome_fantasia', 'cpf_adm' e 'telefone' ficam para ele preencher
        }
        // --- FIM DA LÓGICA CORRIGIDA ---
      },
      error: (err) => {
        // Se der erro (ex: token expirado), desloga e manda para a home
        this.notificationService.show('Faça login para continuar.', 'error');
        this.authService.logout();
        this.router.navigate(['/']);
      }
    });
  }
  
  onSubmit() {
    if (this.isSubmitting) {
      return; // Previne múltiplos envios
    }
    this.isSubmitting = true;

    this.enterpriseService.registerEnterprise(this.enterprise).subscribe({
        next: (response) => {
          console.log('Solicitação de cadastro enviada!', response);
          // Mensagem de sucesso atualizada para o novo fluxo
          this.notificationService.show(
            'Solicitação enviada com sucesso! Iremos notificá-lo por e-mail quando o seu registo for aprovado.',
            "success"
          );
          // Redireciona o utilizador para a página inicial
          this.router.navigate(['/']);
        },
        error: (error) => {
          console.error('Erro ao enviar solicitação de cadastro', error);
          // Exibe a mensagem de erro específica do backend
          const errorMessage = error.error?.detail || 'Ocorreu um erro ao enviar a sua solicitação.';
          this.notificationService.show(errorMessage, "error");
          this.isSubmitting = false; // Reabilita o botão em caso de erro
        },
        complete: () => {
          this.isSubmitting = false; // Reabilita o botão após a conclusão
        }
      });
  }
}