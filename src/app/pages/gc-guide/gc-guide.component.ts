import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { EnterpriseFormData } from '../../models/enterprise.model';

import { FooterComponent } from '../shared/footer/footer.component';
import { EnterpriseService } from '../../../services/enterprise.service';
import { NotificationService } from '../../../services/notification.service';

@Component({
  selector: 'app-gc-guide',
  standalone: true,
  imports: [CommonModule, FormsModule, FooterComponent],
  templateUrl: './gc-guide.component.html',
  styleUrls: ['./gc-guide.component.css']
})
export class GcGuideComponent {
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
    private notificationService: NotificationService
  ) {}

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