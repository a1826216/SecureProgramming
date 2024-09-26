# Debug client for testing the server
# Real client will have additional features included

import asyncio
import json
from websockets.sync.client import connect

# Key pair (hardcoded for now)
rsa_public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuGfdjSJ+GCMwTssD69ind0XUvIS1H/Xr2x7HxLlMM2nQaYyzti3w5OcHvSMd0Ll9drClCw/xKotebE614szcsHXp3q7NJBSj4aMjHtN7lyUe5gteo4L1QNeZCDOMiWTfzRaqLW8/vCK+vDn4/A69Q0svEENoKEvuFZhj2ejJshduuIeuRB5uIa+eAFeeisPscMt1HM8gcypn9mlwBA5Q6OUAOY87b3ouBZzWQLgS3+NFahUhVAft7MPz1flVdb1jBLSJQfMpdVX+yE2Ur4j2sSeNx/QO+g37vm91ZJpNd1iDtMl0O39MVYU4RNiQM8sk2MYYM0NL2tQRXadG6ItH1QIDAQAB"
rsa_private_key = "MIIEpAIBAAKCAQEAuGfdjSJ+GCMwTssD69ind0XUvIS1H/Xr2x7HxLlMM2nQaYyzti3w5OcHvSMd0Ll9drClCw/xKotebE614szcsHXp3q7NJBSj4aMjHtN7lyUe5gteo4L1QNeZCDOMiWTfzRaqLW8/vCK+vDn4/A69Q0svEENoKEvuFZhj2ejJshduuIeuRB5uIa+eAFeeisPscMt1HM8gcypn9mlwBA5Q6OUAOY87b3ouBZzWQLgS3+NFahUhVAft7MPz1flVdb1jBLSJQfMpdVX+yE2Ur4j2sSeNx/QO+g37vm91ZJpNd1iDtMl0O39MVYU4RNiQM8sk2MYYM0NL2tQRXadG6ItH1QIDAQABAoIBAHN6F3NaNjxHTOkKmNoIQlaelCm5sPLivV/qVo8Kun03thti0Oc0vbWaN25pnzIl9jttQu06fnt16xtH7v6n60tVi663KB+ADWAvGL8lEDAGPuMwG4Opbou8d0h7f3ZKhRuZJdht4iueVnLomtK9KCgL3N0CWSdi5SUA2QaMkEHE+CMVW2YG96NHr1IE88EzBZWNE7aQ6zJEcZuNsCZ+KZubCSz6cxrj+aVl81b9ru0fv+pmQDaIw3O/Wrsl+ZxgT1wk3bi0DblLmcwEbcAR2NJZ4lmKdatInqXS2Ns2UKFLiOL6z+KkeWhSPU+uQ3/LOclJg/f7PvxuGOLV4v3qugECgYEA+L/dUegA1o0K4EXWKJuky3wdehvPW86kItcPUpNeLYm3Rygo7zh2LaFx4ojXkWULSuaR2xs/buiZYeVUj4AS5+jziYBOj3/AZcBUkNI6RZHQ5UEeBHaadoyYHyEQXPenbZb4UFaoUzza0BJc7hiKma9biv92tAiEh0rTYF6QGTkCgYEAvcfgXWL8xVPGQmijjtjSor+qoQ6LL1B9qaBN9zBTBPhZtQaZGRTWj9o9XIhdBo1qaTvqAeAZrNk7i+Ldu3cmqj0P+634Zccd6Ya8eOhjZVgcV8NWfsAktk75lA4l9fDLeKIiqb+V0zC+7oXZB+t0FUOLZ5EFo1ndOrkCxcd5r30CgYEA0TnwmngeXFh+EW4sWDOyRUW8NX02yO3iuTtTNA2oZX00n7Fz3OMM5AyrkfOv/ieTfAi8HiOpE0yp1uHiYmFDhbU3Qyyc56540h0YBEgPo3ymzG4dJXvtKFHRkj1pWgkk1tTpQAnjwz+ofOM1Lz+NNP9+bEe8PGn9rx6M9L4VTmECgYAJMm6FGA734R9yiG+ktI1Apdk3BOVp3ZS5a7Nbj1P2obJ3O2Kf/IqJXiIrIdCgSKonf2fPv3R/E+f213+3XgbZqSvlHoEzLXsdnhH0Kg7nEmYNOsIuUlF1JE6kBiuAx7KUngbgAxDXsz0Ngh8Kazas8SEIW9bSG8DE38Jqo0gaYQKBgQD3DyxLo7TMBEAHP5UsneLl5k9IZwLJ816M7JIMDiZU1GWjPvCPunHqcj+2iHYBmsnxzr8FTAhHEcmS1uiH+vjAendQdOsfjz4f9MPKJSr1QKM1oOH9HETJsohJwugEoCtMDqq6+sjWaKuXIoj64rkokdDBHwdHTEMHOde1LUR4Nw=="


signed_data_msg = {
    "type": "signed_data",
    "data": {
        "type": "hello",
        "public_key": rsa_public_key
    },
    "counter": 1,
    "signature": "<Base64 signature of data + counter>"
}

def hello():
    with connect("ws://localhost:8765") as websocket:
        # text = input("enter a message: ")
        websocket.send(json.dumps(signed_data_msg))
        message = websocket.recv()
        print(f"Received: {message}")

hello()


# msg = 