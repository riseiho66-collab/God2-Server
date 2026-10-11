#pragma once
#include "handlers/OwnedBagProjectionService.h"
#include "db/SqliteTradeRepository.h"
#include "db/SqliteBankItemsRepository.h"
namespace god2 {
// CUSTOM-0066: explicit immutable owner proofs; no item eligibility expansion.
struct OwnedBagMutationProof {
    OwnedBagProjectionService* projector;
    SqliteTradeRepository::CommitProof trade(const std::array<SqliteTradeRepository::Snapshot,2>& before,const SqliteTradeRepository::Settlement& after) const {
        const std::array proof{projector->capture_proof(before[0].account,before[0].character),projector->capture_proof(before[1].account,before[1].character)};
        std::array<std::vector<OwnedBagProjectionService::ScalarChange>,2> changes;
        for(unsigned n=0;n<2;++n)for(std::uint8_t slot=0;slot<30;++slot) {
            if(proof[n].snapshot().scalar[slot]!=before[n].bag[slot])throw DatabaseError("Trade bag proof baseline differs");
            if(before[n].bag[slot]!=after.sides[n].bag[slot])changes[n].push_back({slot,before[n].bag[slot],after.sides[n].bag[slot]});
        }
        return {[p=projector,proof]{for(const auto& value:proof)p->verify_proof_in_transaction(value);},
            [p=projector,proof,changes]{for(unsigned n=0;n<2;++n)p->verify_planned_in_transaction(proof[n],changes[n]);}};
    }
    SqliteBankItemsRepository::CommitProof bank(const SqliteBankItemsRepository::Snapshot& before,const SqliteBankItemsRepository::Snapshot& after) const {
        const auto proof=projector->capture_proof(before.account,before.character);
        std::vector<OwnedBagProjectionService::ScalarChange> changes;
        for(std::uint8_t slot=0;slot<30;++slot) {
            if(proof.snapshot().scalar[slot]!=before.bag[slot])throw DatabaseError("Bank bag proof baseline differs");
            if(before.bag[slot]!=after.bag[slot])changes.push_back({slot,before.bag[slot],after.bag[slot]});
        }
        return {[p=projector,proof]{p->verify_proof_in_transaction(proof);},
            [p=projector,proof,changes]{p->verify_planned_in_transaction(proof,changes);}};
    }
};
}
