from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class ProfileStatus(str, Enum):
    """Status of profile completeness"""
    INCOMPLETE = "incomplete"
    PARTIAL = "partial"
    COMPLETE = "complete"
    VERIFIED = "verified"


class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    CIVIL_PARTNERSHIP = "civil_partnership"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class RiskAttitude(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TimeHorizon(str, Enum):
    SHORT_TERM = "short_term"  # < 3 years
    MEDIUM_TERM = "medium_term"  # 3-10 years
    LONG_TERM = "long_term"  # > 10 years


# ============================================================================
# Personal Information
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal and demographic information"""
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: Optional[date] = None
    national_insurance_number: Optional[str] = None
    marital_status: Optional[MaritalStatus] = None
    number_of_dependents: Optional[int] = 0
    
    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Address
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = "United Kingdom"


class Dependent(BaseModel):
    """Information about dependents"""
    name: Optional[str] = None
    relationship: Optional[str] = None  # child, parent, etc.
    date_of_birth: Optional[date] = None
    financially_dependent: bool = True
    notes: Optional[str] = None


# ============================================================================
# Employment & Income
# ============================================================================

class EmploymentDetails(BaseModel):
    """Employment and income information"""
    employment_status: Optional[EmploymentStatus] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    years_in_current_role: Optional[float] = None
    
    # Income
    annual_salary: Optional[float] = None
    bonus_income: Optional[float] = None
    dividend_income: Optional[float] = None
    rental_income: Optional[float] = None
    pension_income: Optional[float] = None
    other_income: Optional[float] = None
    total_annual_income: Optional[float] = None
    
    # Tax
    tax_code: Optional[str] = None
    expected_tax_bracket: Optional[str] = None  # basic, higher, additional


# ============================================================================
# Financial Position
# ============================================================================

class Asset(BaseModel):
    """Individual asset"""
    asset_type: str  # property, ISA, pension, savings, investments, etc.
    description: Optional[str] = None
    current_value: Optional[float] = None
    monthly_contribution: Optional[float] = None
    provider: Optional[str] = None
    account_number: Optional[str] = None
    notes: Optional[str] = None


class Liability(BaseModel):
    """Individual liability/debt"""
    liability_type: str  # mortgage, loan, credit card, etc.
    description: Optional[str] = None
    outstanding_balance: Optional[float] = None
    monthly_payment: Optional[float] = None
    interest_rate: Optional[float] = None
    lender: Optional[str] = None
    term_remaining_months: Optional[int] = None
    notes: Optional[str] = None


class MonthlyExpenses(BaseModel):
    """Breakdown of monthly expenses"""
    housing_mortgage_rent: Optional[float] = None
    utilities: Optional[float] = None
    groceries: Optional[float] = None
    transport: Optional[float] = None
    insurance: Optional[float] = None
    childcare: Optional[float] = None
    entertainment: Optional[float] = None
    subscriptions: Optional[float] = None
    other: Optional[float] = None
    total_monthly_expenses: Optional[float] = None


class FinancialPosition(BaseModel):
    """Current financial situation"""
    assets: List[Asset] = []
    liabilities: List[Liability] = []
    monthly_expenses: Optional[MonthlyExpenses] = None
    
    # Calculated fields
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_worth: Optional[float] = None
    monthly_surplus: Optional[float] = None


# ============================================================================
# Goals & Objectives
# ============================================================================

class FinancialGoal(BaseModel):
    """Individual financial goal"""
    goal_type: str  # retirement, property, education, emergency fund, etc.
    description: str
    target_amount: Optional[float] = None
    target_date: Optional[date] = None
    priority: Optional[int] = None  # 1 = highest
    time_horizon: Optional[TimeHorizon] = None
    notes: Optional[str] = None


class GoalsAndObjectives(BaseModel):
    """Financial goals and planning objectives"""
    primary_goals: List[FinancialGoal] = []
    retirement_age: Optional[int] = None
    desired_retirement_income: Optional[float] = None
    legacy_wishes: Optional[str] = None
    charity_intentions: Optional[str] = None


# ============================================================================
# Risk Profile & Attitudes (Soft Facts)
# ============================================================================

class RiskProfile(BaseModel):
    """Risk tolerance and investment attitudes"""
    risk_attitude: Optional[RiskAttitude] = None
    capacity_for_loss: Optional[str] = None  # description of financial resilience
    investment_experience: Optional[str] = None  # none, limited, experienced, sophisticated
    investment_knowledge_level: Optional[str] = None  # low, medium, high
    
    # Behavioral attitudes
    comfort_with_volatility: Optional[int] = Field(None, ge=1, le=10)  # 1-10 scale
    need_for_access_to_funds: Optional[str] = None  # immediate, medium-term, long-term
    ethical_preferences: Optional[str] = None  # ESG preferences
    
    # Risk questionnaire results
    risk_score: Optional[int] = None
    risk_questionnaire_date: Optional[datetime] = None
    notes: Optional[str] = None


# ============================================================================
# Health & Protection
# ============================================================================

class HealthInfo(BaseModel):
    """Health and protection information"""
    smoker: Optional[bool] = None
    health_conditions: Optional[str] = None
    life_insurance_coverage: Optional[float] = None
    critical_illness_coverage: Optional[float] = None
    income_protection_coverage: Optional[float] = None
    has_will: Optional[bool] = None
    has_lasting_power_of_attorney: Optional[bool] = None


# ============================================================================
# Main Profile Model
# ============================================================================

class FinancialProfile(BaseModel):
    """
    Comprehensive financial profile for FCA-regulated advice.
    Captures both hard facts (concrete data) and soft facts (goals, attitudes).
    """
    # Metadata
    id: Optional[str] = None
    user_id: str
    status: ProfileStatus = ProfileStatus.INCOMPLETE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_reviewed_date: Optional[datetime] = None
    
    # Core sections (Hard Facts)
    personal_info: PersonalInfo
    dependents: List[Dependent] = []
    employment: Optional[EmploymentDetails] = None
    financial_position: Optional[FinancialPosition] = None
    
    # Soft Facts
    goals_and_objectives: Optional[GoalsAndObjectives] = None
    risk_profile: Optional[RiskProfile] = None
    health_and_protection: Optional[HealthInfo] = None
    
    # Additional context
    notes: Optional[str] = None
    advisor_notes: Optional[str] = None
    
    def calculate_completeness(self) -> ProfileStatus:
        """
        Calculate profile completeness based on critical fields.
        This is a simple implementation - can be enhanced with business logic.
        """
        critical_fields_filled = 0
        total_critical_fields = 8
        
        # Check critical hard facts
        if self.personal_info.date_of_birth:
            critical_fields_filled += 1
        if self.employment and self.employment.total_annual_income:
            critical_fields_filled += 1
        if self.financial_position and self.financial_position.net_worth is not None:
            critical_fields_filled += 1
        if self.financial_position and self.financial_position.monthly_expenses:
            critical_fields_filled += 1
            
        # Check critical soft facts
        if self.goals_and_objectives and self.goals_and_objectives.primary_goals:
            critical_fields_filled += 1
        if self.risk_profile and self.risk_profile.risk_attitude:
            critical_fields_filled += 1
        if self.goals_and_objectives and self.goals_and_objectives.retirement_age:
            critical_fields_filled += 1
        if self.employment and self.employment.employment_status:
            critical_fields_filled += 1
            
        # Determine status
        if critical_fields_filled == 0:
            return ProfileStatus.INCOMPLETE
        elif critical_fields_filled < total_critical_fields * 0.7:
            return ProfileStatus.PARTIAL
        elif critical_fields_filled >= total_critical_fields:
            return ProfileStatus.COMPLETE
        else:
            return ProfileStatus.PARTIAL
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "status": "partial",
                "personal_info": {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1985-06-15",
                    "email": "john.smith@example.com"
                },
                "employment": {
                    "employment_status": "employed",
                    "annual_salary": 50000
                },
                "goals_and_objectives": {
                    "primary_goals": [
                        {
                            "goal_type": "retirement",
                            "description": "Retire comfortably at 65",
                            "target_amount": 1000000
                        }
                    ]
                }
            }
        }
