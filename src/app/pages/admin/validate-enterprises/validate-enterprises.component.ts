import { Component, OnInit } from '@angular/core';
import { Enterprise } from '../../../models/enterprise.model';
import { EnterpriseService } from '../../../../services/enterprise.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NotificationService } from '../../../../services/notification.service';

@Component({
  selector: 'app-validate-enterprises',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './validate-enterprises.component.html',
  styleUrls: ['./validate-enterprises.component.css']
})
export class ValidateEnterprisesComponent implements OnInit {
  pendingEnterprises: Enterprise[] = [];
  approvedEnterprises: Enterprise[] = [];
  rejectedEnterprises: Enterprise[] = [];
  
  isRejectionModalVisible = false;
  rejectionReason = '';
  enterpriseToRejectId: number | null = null;
  isLoading = false;

  constructor(
    private enterpriseService: EnterpriseService,
    private notificationService: NotificationService
  ) { }

  ngOnInit(): void {
    this.loadAllEnterprises();
  }

  loadAllEnterprises(): void {
    this.isLoading = true;
    // Carrega as empresas pendentes
    this.enterpriseService.getEnterprisesByStatus('PENDING').subscribe({
      next: (data) => this.pendingEnterprises = data,
      error: (err) => console.error('Erro ao buscar empresas pendentes', err)
    });

    // Carrega as empresas aprovadas
    this.enterpriseService.getEnterprisesByStatus('APPROVED').subscribe({
      next: (data) => this.approvedEnterprises = data,
      error: (err) => console.error('Erro ao buscar empresas aprovadas', err)
    });

    // Carrega as empresas rejeitadas e finaliza o loading
    this.enterpriseService.getEnterprisesByStatus('REJECTED').subscribe({
      next: (data) => {
        this.rejectedEnterprises = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erro ao buscar empresas rejeitadas', err);
        this.isLoading = false;
      }
    });
  }

  approve(enterpriseId: number): void {
    this.enterpriseService.approveEnterprise(enterpriseId).subscribe({
      next: () => {
        this.notificationService.show('Empresa aprovada com sucesso!', 'success');
        this.loadAllEnterprises();
      },
      error: (err) => {
        this.notificationService.show('Erro ao aprovar empresa.', 'error');
        console.error('Erro ao aprovar empresa', err);
      }
    });
  }

  openRejectionModal(enterpriseId: number): void {
    this.enterpriseToRejectId = enterpriseId;
    this.isRejectionModalVisible = true;
  }

  cancelRejection(): void {
    this.isRejectionModalVisible = false;
    this.rejectionReason = '';
    this.enterpriseToRejectId = null;
  }

  confirmRejection(): void {
    if (!this.rejectionReason.trim()) {
      this.notificationService.show('Por favor, insira um motivo para a rejeição.', 'warning');
      return;
    }

    if (this.enterpriseToRejectId) {
      this.enterpriseService.rejectEnterprise(this.enterpriseToRejectId, this.rejectionReason)
        .subscribe({
          next: () => {
            this.notificationService.show('Empresa rejeitada com sucesso.', 'info');
            this.cancelRejection();
            this.loadAllEnterprises();
          },
          error: (err) => {
            this.notificationService.show('Erro ao rejeitar empresa.', 'error');
            console.error('Erro ao rejeitar empresa', err);
          }
        });
    }
  }
}