from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session

# from services.companies.company_services import CompanyClient
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import (
    get_deal_service,
    get_lead_service,
    get_product_service,
)
from services.dependencies.dependencies_bitrix_entity import (
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_product_bitrix_client,
)
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_repo_entity import (
    get_product_image_repo,
)
from services.leads.lead_services import LeadClient
from services.product_images.product_image_repository import (
    ProductImageRepository,
)
from services.products.product_bitrix_services import ProductBitrixClient
from services.products.product_services import ProductClient

# from schemas.product_schemas import FieldValue, ProductUpdate


# from services.users.user_bitrix_services import UserBitrixClient

# from services.users.user_services import UserClient

test_router = APIRouter(dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check",
    description="Information about.",
)  # type: ignore
async def check(
    id_entity: int | str | None = None,
    redis: Redis = Depends(get_redis_session),
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client
    ),
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_client: DealClient = Depends(get_deal_service),
    lead_client: LeadClient = Depends(get_lead_service),
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client
    ),
    product_image_repo: ProductImageRepository = Depends(
        get_product_image_repo
    ),
    product_client: ProductClient = Depends(get_product_service),
) -> JSONResponse:
    external_id = 0
    try:
        ...
        from core.logger import logger
        from schemas.enums import SourcesProductEnum

        image_dict = {
            "4hvpbfvxsns0lq2rsq16vj03pjwx6mrm.jpg": (
                "https://matest.kz/upload/iblock/1a4/"
                "4hvpbfvxsns0lq2rsq16vj03pjwx6mrm.jpg"
            ),
            "3wwvolwuzhyyhb7esxmu0jpolbs68rz1.jpg": (
                "https://matest.kz/upload/iblock/bd0/"
                "3wwvolwuzhyyhb7esxmu0jpolbs68rz1.jpg"
            ),
            "63lvhhuy9umdn20b88d5zc9vw9k10oh6.jpg": (
                "https://matest.kz/upload/iblock/483/"
                "63lvhhuy9umdn20b88d5zc9vw9k10oh6.jpg"
            ),
            "0ywj1zl1si8nqfmaj5kodq7v9hx0s84c.jpg": (
                "https://matest.kz/upload/iblock/9ef/"
                "0ywj1zl1si8nqfmaj5kodq7v9hx0s84c.jpg"
            ),
            "rjvkf5fleniscu0588cnmyzw2kdi3jve.jpg": (
                "https://matest.kz/upload/iblock/d1d/"
                "rjvkf5fleniscu0588cnmyzw2kdi3jve.jpg"
            ),
            "2e2vgn7u3o1x0zfovi0pxcwbd50zp2gc.jpg": (
                "https://matest.kz/upload/iblock/5be/"
                "2e2vgn7u3o1x0zfovi0pxcwbd50zp2gc.jpg"
            ),
            "t3z8gkn2yhakv6r2mbw76xcf5zgug3o1.jpg": (
                "https://matest.kz/upload/iblock/2a1/"
                "t3z8gkn2yhakv6r2mbw76xcf5zgug3o1.jpg"
            ),
            "ql3eurge6igzdsnb1rmau719eojfx4a5.jpg": (
                "https://matest.kz/upload/iblock/4bb/"
                "ql3eurge6igzdsnb1rmau719eojfx4a5.jpg"
            ),
            "81mshvpe32f9s0ecqf42zbv39527bmaa.jpg": (
                "https://matest.kz/upload/iblock/7ba/"
                "81mshvpe32f9s0ecqf42zbv39527bmaa.jpg"
            ),
            "xq599ysc28580e192s6ijzmrrlqe22e3.jpg": (
                "https://matest.kz/upload/iblock/4a3/"
                "xq599ysc28580e192s6ijzmrrlqe22e3.jpg"
            ),
            "besx2oz2g23qz4h0o6arqpv2c0uf9xx4.jpg": (
                "https://matest.kz/upload/iblock/283/"
                "besx2oz2g23qz4h0o6arqpv2c0uf9xx4.jpg"
            ),
            "6evo04f4qsrvnf3yn6y64v6tqes3qxnl.jpg": (
                "https://matest.kz/upload/iblock/0e1/"
                "6evo04f4qsrvnf3yn6y64v6tqes3qxnl.jpg"
            ),
            "u6q04xnaxerr8q4dqlgehhs1ba9d1oxt.jpg": (
                "https://matest.kz/upload/iblock/183/"
                "u6q04xnaxerr8q4dqlgehhs1ba9d1oxt.jpg"
            ),
            "8pr00km2a1vyirs88et9xnjg67tqvls2.jpg": (
                "https://matest.kz/upload/iblock/51c/"
                "8pr00km2a1vyirs88et9xnjg67tqvls2.jpg"
            ),
            "rp1lompvifqnfq2uj158udwnu32fs7gf.jpg": (
                "https://matest.kz/upload/iblock/ff5/"
                "rp1lompvifqnfq2uj158udwnu32fs7gf.jpg"
            ),
            "g2mgsv417pp3g535slrbn23u04enop39.jpg": (
                "https://matest.kz/upload/iblock/f4b/"
                "g2mgsv417pp3g535slrbn23u04enop39.jpg"
            ),
            "0k1iaec34tn0iaj2w3u7h70gfbh1gsmq.jpg": (
                "https://matest.kz/upload/iblock/d95/"
                "0k1iaec34tn0iaj2w3u7h70gfbh1gsmq.jpg"
            ),
            "cb8q16b0shntu95fla80eww4clck6gxl.jpg": (
                "https://matest.kz/upload/iblock/825/"
                "cb8q16b0shntu95fla80eww4clck6gxl.jpg"
            ),
            "62l3ykq20978pz2nyq3dhap6ps6sct5g.jpg": (
                "https://matest.kz/upload/iblock/2c5/"
                "62l3ykq20978pz2nyq3dhap6ps6sct5g.jpg"
            ),
            "61eadeqrt8j1ci9p5dytu8e270klbny3.jpg": (
                "https://matest.kz/upload/iblock/ed6/"
                "61eadeqrt8j1ci9p5dytu8e270klbny3.jpg"
            ),
            "640m315tl2yz6oqxh3cxl5tst7k32vzw.jpg": (
                "https://matest.kz/upload/iblock/f3c/"
                "640m315tl2yz6oqxh3cxl5tst7k32vzw.jpg"
            ),
            "47j4f0dsg0plmdyx5r2s0mxvwldyjcjk.jpg": (
                "https://matest.kz/upload/iblock/aeb/"
                "47j4f0dsg0plmdyx5r2s0mxvwldyjcjk.jpg"
            ),
            "bd7w2v8dnv9brlj32bw137njz86bgeqx.jpg": (
                "https://matest.kz/upload/iblock/28e/"
                "bd7w2v8dnv9brlj32bw137njz86bgeqx.jpg"
            ),
            "s00dtd4nrz4niwr3sehw21hbwlx72rdz.jpg": (
                "https://matest.kz/upload/iblock/301/"
                "s00dtd4nrz4niwr3sehw21hbwlx72rdz.jpg"
            ),
            "io0dm7324kqpku0sxqthfxn5efge1xqs.jpg": (
                "https://matest.kz/upload/iblock/345/"
                "io0dm7324kqpku0sxqthfxn5efge1xqs.jpg"
            ),
            "9xpeqnjavwtgklzre3ixand8c0wr1zi2.jpg": (
                "https://matest.kz/upload/iblock/0ba/"
                "9xpeqnjavwtgklzre3ixand8c0wr1zi2.jpg"
            ),
            "usxj4fdedhhhfuhn8rcbh0520cvlrv4p.jpg": (
                "https://matest.kz/upload/iblock/28e/"
                "usxj4fdedhhhfuhn8rcbh0520cvlrv4p.jpg"
            ),
            "2iynmg0gpnjqgo4xxim3zb62bduu0rvd.jpg": (
                "https://matest.kz/upload/iblock/7ab/"
                "2iynmg0gpnjqgo4xxim3zb62bduu0rvd.jpg"
            ),
            "2qx3h4okpbicqcj3e9gz736yw7uav72s.jpg": (
                "https://matest.kz/upload/iblock/d2f/"
                "2qx3h4okpbicqcj3e9gz736yw7uav72s.jpg"
            ),
            "neh0739gadszvzw3d06z4c07rqwx9ntc.jpg": (
                "https://matest.kz/upload/iblock/6b9/"
                "neh0739gadszvzw3d06z4c07rqwx9ntc.jpg"
            ),
            "w22v25jaqjugckvspl3z5qntsfxxmmm3.jpg": (
                "https://matest.kz/upload/iblock/10b/"
                "w22v25jaqjugckvspl3z5qntsfxxmmm3.jpg"
            ),
            "dcnj9m72tv7ooiuktzbf0gqdlf5u8hxw.jpg": (
                "https://matest.kz/upload/iblock/003/"
                "dcnj9m72tv7ooiuktzbf0gqdlf5u8hxw.jpg"
            ),
            "kleod2th9ltx1vsiyjbuodpve1ij6xsg.jpg": (
                "https://matest.kz/upload/iblock/8aa/"
                "kleod2th9ltx1vsiyjbuodpve1ij6xsg.jpg"
            ),
            "ikpa57s9u2kumbaf2rzmnllwrw8aqe57.jpg": (
                "https://matest.kz/upload/iblock/620/"
                "ikpa57s9u2kumbaf2rzmnllwrw8aqe57.jpg"
            ),
            "45xwb3z15vviahdglsseovt3zxoe4muc.jpg": (
                "https://matest.kz/upload/iblock/9da/"
                "45xwb3z15vviahdglsseovt3zxoe4muc.jpg"
            ),
            "nezo5x5q82254opva2efw7fupkl92njm.jpg": (
                "https://matest.kz/upload/iblock/165/"
                "nezo5x5q82254opva2efw7fupkl92njm.jpg"
            ),
            "eadhg2ihpw3p5fs1ynrh81dzueaclcwm.jpg": (
                "https://matest.kz/upload/iblock/ecc/"
                "eadhg2ihpw3p5fs1ynrh81dzueaclcwm.jpg"
            ),
            "2lz66rkh1lmf5glnce80l7atqrv7501i.jpg": (
                "https://matest.kz/upload/iblock/0da/"
                "2lz66rkh1lmf5glnce80l7atqrv7501i.jpg"
            ),
            "arigemt1nko26aqk6nysxlpn19mz496y.jpg": (
                "https://matest.kz/upload/iblock/a1a/"
                "arigemt1nko26aqk6nysxlpn19mz496y.jpg"
            ),
            "h54m301bflrzwk9dg5roa4afebxhq9aq.jpg": (
                "https://matest.kz/upload/iblock/547/"
                "h54m301bflrzwk9dg5roa4afebxhq9aq.jpg"
            ),
            "xodgzcmkvqxpxybf5xu4snknft591k7h.jpg": (
                "https://matest.kz/upload/iblock/be8/"
                "xodgzcmkvqxpxybf5xu4snknft591k7h.jpg"
            ),
            "kztwjtmums5wp3c1mmblk1z3dnk2afj6.jpg": (
                "https://matest.kz/upload/iblock/80a/"
                "kztwjtmums5wp3c1mmblk1z3dnk2afj6.jpg"
            ),
            "9f0d9nzrczphjr8k49u6b3vgipykarhb.jpg": (
                "https://matest.kz/upload/iblock/4c2/"
                "9f0d9nzrczphjr8k49u6b3vgipykarhb.jpg"
            ),
            "2qvg28p41dd8g5yo72ua1nryw5bpenhz.jpg": (
                "https://matest.kz/upload/iblock/b8b/"
                "2qvg28p41dd8g5yo72ua1nryw5bpenhz.jpg"
            ),
            "ua7htzdimrvbzw6wkyq682gp9igwx3al.jpg": (
                "https://matest.kz/upload/iblock/b24/"
                "ua7htzdimrvbzw6wkyq682gp9igwx3al.jpg"
            ),
            "yf8nbkgravg0eap38gjqho0ae3dfpvb9.jpg": (
                "https://matest.kz/upload/iblock/de6/"
                "yf8nbkgravg0eap38gjqho0ae3dfpvb9.jpg"
            ),
            "jwvw7t5o1iigw3zynvqmhkl13gqa7r2n.jpg": (
                "https://matest.kz/upload/iblock/bdf/"
                "jwvw7t5o1iigw3zynvqmhkl13gqa7r2n.jpg"
            ),
            "nlm2qjv5c2orgyjqrdk2mfz98lg7jnmy.jpg": (
                "https://matest.kz/upload/iblock/9d0/"
                "nlm2qjv5c2orgyjqrdk2mfz98lg7jnmy.jpg"
            ),
            "e0tlkka956myfq8hi7fxt2xtt0wtyq1g.jpg": (
                "https://matest.kz/upload/iblock/a80/"
                "e0tlkka956myfq8hi7fxt2xtt0wtyq1g.jpg"
            ),
            "fj27oleep9otz9a9mkwfapop5ehtmj2h.jpg": (
                "https://matest.kz/upload/iblock/9e1/"
                "fj27oleep9otz9a9mkwfapop5ehtmj2h.jpg"
            ),
            "gg3dztxl3iokezyl31b6b4pzjoz2cskj.jpg": (
                "https://matest.kz/upload/iblock/231/"
                "gg3dztxl3iokezyl31b6b4pzjoz2cskj.jpg"
            ),
            "qogyog1xiu331bksieuecjl9lwsc30mx.jpg": (
                "https://matest.kz/upload/iblock/05c/"
                "qogyog1xiu331bksieuecjl9lwsc30mx.jpg"
            ),
            "yomucod678ufx0i1zwxhrogl4baiud9r.jpg": (
                "https://matest.kz/upload/iblock/620/"
                "yomucod678ufx0i1zwxhrogl4baiud9r.jpg"
            ),
            "3nre3plpj6zimrnw6478ylp8n8x0a9k1.jpg": (
                "https://matest.kz/upload/iblock/0f7/"
                "3nre3plpj6zimrnw6478ylp8n8x0a9k1.jpg"
            ),
            "tc0prv77pclwbmpnjsq18qop5hzo6ji2.jpg": (
                "https://matest.kz/upload/iblock/c97/"
                "tc0prv77pclwbmpnjsq18qop5hzo6ji2.jpg"
            ),
            "z1xo7uig4xlspn5pv519i2b4hyafb8qh.jpg": (
                "https://matest.kz/upload/iblock/64f/"
                "z1xo7uig4xlspn5pv519i2b4hyafb8qh.jpg"
            ),
            "d1fdbzkq219mf45z67bjsrqsp7vnmgig.jpg": (
                "https://matest.kz/upload/iblock/648/"
                "d1fdbzkq219mf45z67bjsrqsp7vnmgig.jpg"
            ),
            "b6sz6kx2vxfmbr0jlvge9u005whf32yi.jpg": (
                "https://matest.kz/upload/iblock/f16/"
                "b6sz6kx2vxfmbr0jlvge9u005whf32yi.jpg"
            ),
            "0gxxa3gym0zgyge9h5jmfddtnomd7usb.jpg": (
                "https://matest.kz/upload/iblock/c5e/"
                "0gxxa3gym0zgyge9h5jmfddtnomd7usb.jpg"
            ),
            "1wlj6nfavt9yo17ftgkejb7oahpr8oy4.jpg": (
                "https://matest.kz/upload/iblock/1ec/"
                "1wlj6nfavt9yo17ftgkejb7oahpr8oy4.jpg"
            ),
            "hho8iniboa1wp97n4yp00enzlbe29umw.jpg": (
                "https://matest.kz/upload/iblock/e38/"
                "hho8iniboa1wp97n4yp00enzlbe29umw.jpg"
            ),
            "2nimdgbqf6kaqj17m62ftn9ogebgmcud.jpg": (
                "https://matest.kz/upload/iblock/4dd/"
                "2nimdgbqf6kaqj17m62ftn9ogebgmcud.jpg"
            ),
            "gdf9hdwzyabngycpecm30rpljism3abo.jpg": (
                "https://matest.kz/upload/iblock/0d5/"
                "gdf9hdwzyabngycpecm30rpljism3abo.jpg"
            ),
            "qj87pld35cfr5sl8ytzparx0j1ufp0hf.jpg": (
                "https://matest.kz/upload/iblock/506/"
                "qj87pld35cfr5sl8ytzparx0j1ufp0hf.jpg"
            ),
            "yi0v0lesjbql4mjnb4obxk0ty0m05o2c.jpg": (
                "https://matest.kz/upload/iblock/ee5/"
                "yi0v0lesjbql4mjnb4obxk0ty0m05o2c.jpg"
            ),
            "qgoga1xx2no8n4ua6v762xv3gcd3dd9e.jpg": (
                "https://matest.kz/upload/iblock/88e/"
                "qgoga1xx2no8n4ua6v762xv3gcd3dd9e.jpg"
            ),
            "f9j4hef21bhwn7qi0ok0yj41p7uuqjuu.jpg": (
                "https://matest.kz/upload/iblock/67a/"
                "f9j4hef21bhwn7qi0ok0yj41p7uuqjuu.jpg"
            ),
            "hx549ezyhtm4suxnlyzq6elxitwf129j.jpg": (
                "https://matest.kz/upload/iblock/bec/"
                "hx549ezyhtm4suxnlyzq6elxitwf129j.jpg"
            ),
            "o9jtc47w7jdyd554gegrhtmy13sqkple.jpg": (
                "https://matest.kz/upload/iblock/f16/"
                "o9jtc47w7jdyd554gegrhtmy13sqkple.jpg"
            ),
            "c6sk8wx1q7rs14eh5fb90y2og1i1efqr.jpg": (
                "https://matest.kz/upload/iblock/1c8/"
                "c6sk8wx1q7rs14eh5fb90y2og1i1efqr.jpg"
            ),
            "fpcm7ph6qw4w0al112e2gqr7h3eknqc6.jpg": (
                "https://matest.kz/upload/iblock/6c4/"
                "fpcm7ph6qw4w0al112e2gqr7h3eknqc6.jpg"
            ),
            "j8iixh9wcq2kabezidwhgezr5jcica3v.jpg": (
                "https://matest.kz/upload/iblock/322/"
                "j8iixh9wcq2kabezidwhgezr5jcica3v.jpg"
            ),
            "px1nbkzwr1n3g7ocbtha61mby6slmyut.jpg": (
                "https://matest.kz/upload/iblock/a3e/"
                "px1nbkzwr1n3g7ocbtha61mby6slmyut.jpg"
            ),
            "pj0ix6it75pn876ldnhcmnc81phvvvey.jpg": (
                "https://matest.kz/upload/iblock/28f/"
                "pj0ix6it75pn876ldnhcmnc81phvvvey.jpg"
            ),
            "xvqv3qc4ufn504llyv9vazet9dra2na5.jpg": (
                "https://matest.kz/upload/iblock/c98/"
                "xvqv3qc4ufn504llyv9vazet9dra2na5.jpg"
            ),
            "hai2y9yzeciv2mbu2gljznlvvrik0e0m.jpg": (
                "https://matest.kz/upload/iblock/417/"
                "hai2y9yzeciv2mbu2gljznlvvrik0e0m.jpg"
            ),
            "qxrnjhmpzlavunh56fqfwqr8jsmmgx4l.jpg": (
                "https://matest.kz/upload/iblock/206/"
                "qxrnjhmpzlavunh56fqfwqr8jsmmgx4l.jpg"
            ),
            "9j4xt8w5gqtefykv3nyn3wci1wdne1bz.jpg": (
                "https://matest.kz/upload/iblock/5e2/"
                "9j4xt8w5gqtefykv3nyn3wci1wdne1bz.jpg"
            ),
            "1pder8xm6fh2uezwlk6lfpvmo589m8i8.jpg": (
                "https://matest.kz/upload/iblock/8a9/"
                "1pder8xm6fh2uezwlk6lfpvmo589m8i8.jpg"
            ),
            "tuyhxv6zp7hs1nlpa32862wmvf6t8zz3.jpg": (
                "https://matest.kz/upload/iblock/cb1/"
                "tuyhxv6zp7hs1nlpa32862wmvf6t8zz3.jpg"
            ),
            "tila0zmc11inl5i2z4km9jb3h22eonvj.jpg": (
                "https://matest.kz/upload/iblock/43c/"
                "tila0zmc11inl5i2z4km9jb3h22eonvj.jpg"
            ),
            "7jt2tjqhcmiy3vd7an1litlf6c42kgdk.jpg": (
                "https://matest.kz/upload/iblock/5dd/"
                "7jt2tjqhcmiy3vd7an1litlf6c42kgdk.jpg"
            ),
            "d3h7hye3dy2ckem4y3it848jjral60uo.jpg": (
                "https://matest.kz/upload/iblock/da3/"
                "d3h7hye3dy2ckem4y3it848jjral60uo.jpg"
            ),
            "98eer1lwl0asu7e0vqq90ib0haxci61p.jpg": (
                "https://matest.kz/upload/iblock/791/"
                "98eer1lwl0asu7e0vqq90ib0haxci61p.jpg"
            ),
            "tmuytay41eh9uealc0pngizty0sev5a9.jpg": (
                "https://matest.kz/upload/iblock/de2/"
                "tmuytay41eh9uealc0pngizty0sev5a9.jpg"
            ),
            "fy7h30wwwh3ijusqok5al1sa5d0pi0dy.jpg": (
                "https://matest.kz/upload/iblock/2c6/"
                "fy7h30wwwh3ijusqok5al1sa5d0pi0dy.jpg"
            ),
            "x9h68djozusht5ueg5ozq57hrvkfpdyl.jpg": (
                "https://matest.kz/upload/iblock/321/"
                "x9h68djozusht5ueg5ozq57hrvkfpdyl.jpg"
            ),
            "78faecs93onaieu4fm2jk35u5s20n2g8.jpg": (
                "https://matest.kz/upload/iblock/a90/"
                "78faecs93onaieu4fm2jk35u5s20n2g8.jpg"
            ),
            "unp2alko58hsa62r31yz82jth1rpobrh.jpg": (
                "https://matest.kz/upload/iblock/52e/"
                "unp2alko58hsa62r31yz82jth1rpobrh.jpg"
            ),
            "0fq8hb30uvfkoxq2b5a4arz4clm1v2w9.jpg": (
                "https://matest.kz/upload/iblock/036/"
                "0fq8hb30uvfkoxq2b5a4arz4clm1v2w9.jpg"
            ),
            "inmf4a1nveqw10n9ek2tsadv5bvhu3r3.jpg": (
                "https://matest.kz/upload/iblock/b32/"
                "inmf4a1nveqw10n9ek2tsadv5bvhu3r3.jpg"
            ),
            "vm063e4hddjex43pff0l0y7i7q7giyp8.jpg": (
                "https://matest.kz/upload/iblock/c22/"
                "vm063e4hddjex43pff0l0y7i7q7giyp8.jpg"
            ),
            "5fgacp4wc4mmhng5jjzazzo2gb6vbxld.jpg": (
                "https://matest.kz/upload/iblock/285/"
                "5fgacp4wc4mmhng5jjzazzo2gb6vbxld.jpg"
            ),
            "ph1x1n9ep7wptz9rvbwruwy3oy3cfjwn.jpg": (
                "https://matest.kz/upload/iblock/2e3/"
                "ph1x1n9ep7wptz9rvbwruwy3oy3cfjwn.jpg"
            ),
            "eiabzpwv2ofl3gbiv3zt06vq42a04lpt.jpg": (
                "https://matest.kz/upload/iblock/d3a/"
                "eiabzpwv2ofl3gbiv3zt06vq42a04lpt.jpg"
            ),
            "gbmf4mv83aehrr965gpdcwcap80hzy3k.jpg": (
                "https://matest.kz/upload/iblock/30e/"
                "gbmf4mv83aehrr965gpdcwcap80hzy3k.jpg"
            ),
            "gb9ncn81u7wxj65hldre21bxkxvzmqcs.jpg": (
                "https://matest.kz/upload/iblock/8c0/"
                "gb9ncn81u7wxj65hldre21bxkxvzmqcs.jpg"
            ),
            "awb8j9o36rk86dwhugb7fx9y2egnf0p3.jpg": (
                "https://matest.kz/upload/iblock/92f/"
                "awb8j9o36rk86dwhugb7fx9y2egnf0p3.jpg"
            ),
            "89iibwxh8llsa3hzpuf7fa30e5mjhri9.jpg": (
                "https://matest.kz/upload/iblock/edb/"
                "89iibwxh8llsa3hzpuf7fa30e5mjhri9.jpg"
            ),
            "z3d3uq8gwq8cueggqr2g2rl6axt89niu.jpg": (
                "https://matest.kz/upload/iblock/ae0/"
                "z3d3uq8gwq8cueggqr2g2rl6axt89niu.jpg"
            ),
            "1t9g3l1rzm2bkrobco0lsdykjp5q6nww.jpg": (
                "https://matest.kz/upload/iblock/c15/"
                "1t9g3l1rzm2bkrobco0lsdykjp5q6nww.jpg"
            ),
            "etujlr8acoeqn1nxyggatutcciiodlgp.jpg": (
                "https://matest.kz/upload/iblock/8de/"
                "etujlr8acoeqn1nxyggatutcciiodlgp.jpg"
            ),
            "zx9yc20js9kjbku2f0sl1gilawrm9bkm.jpg": (
                "https://matest.kz/upload/iblock/0bd/"
                "zx9yc20js9kjbku2f0sl1gilawrm9bkm.jpg"
            ),
            "qzh5ze6wun6h5pv8edu8gdxfzkvb3mp7.jpg": (
                "https://matest.kz/upload/iblock/c78/"
                "qzh5ze6wun6h5pv8edu8gdxfzkvb3mp7.jpg"
            ),
            "wly3yjsjgafh69jm5ehvr86rxyi3g64f.jpg": (
                "https://matest.kz/upload/iblock/6e6/"
                "wly3yjsjgafh69jm5ehvr86rxyi3g64f.jpg"
            ),
            "cvcob1nso6xa2ooqp8xgmr0e6cxiclyy.jpg": (
                "https://matest.kz/upload/iblock/ad9/"
                "cvcob1nso6xa2ooqp8xgmr0e6cxiclyy.jpg"
            ),
            "ifekri617y998jux7bc7h0hcjf7gpfpg.jpg": (
                "https://matest.kz/upload/iblock/24c/"
                "ifekri617y998jux7bc7h0hcjf7gpfpg.jpg"
            ),
            "0io28t3r0k643l0dji7nkjaz1l3dho3a.jpg": (
                "https://matest.kz/upload/iblock/557/"
                "0io28t3r0k643l0dji7nkjaz1l3dho3a.jpg"
            ),
            "fe4q7j96wr25xa10tlk7fuuqjzbf2k6k.jpg": (
                "https://matest.kz/upload/iblock/8a0/"
                "fe4q7j96wr25xa10tlk7fuuqjzbf2k6k.jpg"
            ),
            "6brflqv7g881ua3c8cwxtvlalvi1jib5.jpg": (
                "https://matest.kz/upload/iblock/c69/"
                "6brflqv7g881ua3c8cwxtvlalvi1jib5.jpg"
            ),
            "a632cktkuk3bkvfe5sss4o2prc2j8qep.jpg": (
                "https://matest.kz/upload/iblock/ace/"
                "a632cktkuk3bkvfe5sss4o2prc2j8qep.jpg"
            ),
            "l6eydxrypa9k54noa9g0z5dlx7efhkzx.jpg": (
                "https://matest.kz/upload/iblock/77b/"
                "l6eydxrypa9k54noa9g0z5dlx7efhkzx.jpg"
            ),
            "c9fr65sl7kbc1hkxqhrt6wa6h5p53w43.jpg": (
                "https://matest.kz/upload/iblock/5e1/"
                "c9fr65sl7kbc1hkxqhrt6wa6h5p53w43.jpg"
            ),
            "oe02cb5orxwngkesaapepnm0vt5jb6u1.jpg": (
                "https://matest.kz/upload/iblock/d85/"
                "oe02cb5orxwngkesaapepnm0vt5jb6u1.jpg"
            ),
            "wyudm9zapij0gfslrciqpd41svr9xy01.jpg": (
                "https://matest.kz/upload/iblock/220/"
                "wyudm9zapij0gfslrciqpd41svr9xy01.jpg"
            ),
            "vil6evdx4vmtzsmaefxkaht4sk4gvmu5.jpg": (
                "https://matest.kz/upload/iblock/879/"
                "vil6evdx4vmtzsmaefxkaht4sk4gvmu5.jpg"
            ),
            "yfbt7kqs353hllg2x3xepsc6b3fxksc6.jpg": (
                "https://matest.kz/upload/iblock/b68/"
                "yfbt7kqs353hllg2x3xepsc6b3fxksc6.jpg"
            ),
            "hsr8fbj254jel9zktr1yfdjgyjy5yndd.jpg": (
                "https://matest.kz/upload/iblock/5de/"
                "hsr8fbj254jel9zktr1yfdjgyjy5yndd.jpg"
            ),
            "sd4ausp697hnyt5t9uely60lwfutzod4.jpg": (
                "https://matest.kz/upload/iblock/d3f/"
                "sd4ausp697hnyt5t9uely60lwfutzod4.jpg"
            ),
            "hdhfzsaay1sghvsrpt9wc2qd852yeb5o.jpg": (
                "https://matest.kz/upload/iblock/903/"
                "hdhfzsaay1sghvsrpt9wc2qd852yeb5o.jpg"
            ),
            "e6qvrf2h85uxw7npmppjt9quf5rf2x2h.jpg": (
                "https://matest.kz/upload/iblock/2ff/"
                "e6qvrf2h85uxw7npmppjt9quf5rf2x2h.jpg"
            ),
            "6xt6j31k2nk3yio1k3kq1yl1x52totj8.jpg": (
                "https://matest.kz/upload/iblock/07c/"
                "6xt6j31k2nk3yio1k3kq1yl1x52totj8.jpg"
            ),
            "3kd4h5a2of33np83tyax8z4ekgk3siat.jpg": (
                "https://matest.kz/upload/iblock/ef1/"
                "3kd4h5a2of33np83tyax8z4ekgk3siat.jpg"
            ),
            "0vu0wipdtjz579f1uz0c48xkigqm9l5e.jpg": (
                "https://matest.kz/upload/iblock/6ce/"
                "0vu0wipdtjz579f1uz0c48xkigqm9l5e.jpg"
            ),
            "0ibuy1btttw573zkg9uu3znm35h16dev.jpg": (
                "https://matest.kz/upload/iblock/468/"
                "0ibuy1btttw573zkg9uu3znm35h16dev.jpg"
            ),
            "c9vse0jmps8bxmef0qsnpl7kfxvdufy2.jpg": (
                "https://matest.kz/upload/iblock/29b/"
                "c9vse0jmps8bxmef0qsnpl7kfxvdufy2.jpg"
            ),
            "8ti105u0vrhnx06k4r9mpb0vaksulm2o.jpg": (
                "https://matest.kz/upload/iblock/6fc/"
                "8ti105u0vrhnx06k4r9mpb0vaksulm2o.jpg"
            ),
            "1xzcyrh6qebp7oxp31b37iw2dued3khq.jpg": (
                "https://matest.kz/upload/iblock/293/"
                "1xzcyrh6qebp7oxp31b37iw2dued3khq.jpg"
            ),
            "gj9ju6rsma1sunmr0b5n5v3adyhtd68f.jpg": (
                "https://matest.kz/upload/iblock/00c/"
                "gj9ju6rsma1sunmr0b5n5v3adyhtd68f.jpg"
            ),
            "cv9mq3244y5qb3l096yh68n0r8wn3wvs.jpg": (
                "https://matest.kz/upload/iblock/b83/"
                "cv9mq3244y5qb3l096yh68n0r8wn3wvs.jpg"
            ),
            "uhozy241pt3jz2kniy4lm93xza98r552.jpg": (
                "https://matest.kz/upload/iblock/4d4/"
                "uhozy241pt3jz2kniy4lm93xza98r552.jpg"
            ),
            "je75uarwftvtqi330kmnz20cp4pqqg0r.jpg": (
                "https://matest.kz/upload/iblock/733/"
                "je75uarwftvtqi330kmnz20cp4pqqg0r.jpg"
            ),
            "w1ry0ayfsuskyfc889d565fjgxjbmuga.jpg": (
                "https://matest.kz/upload/iblock/89f/"
                "w1ry0ayfsuskyfc889d565fjgxjbmuga.jpg"
            ),
            "j0xpwd5cncs7dcaxipxoepuyfiamhqh1.jpg": (
                "https://matest.kz/upload/iblock/a1d/"
                "j0xpwd5cncs7dcaxipxoepuyfiamhqh1.jpg"
            ),
            "jrynmeif6iziza2djdiblxxcvg7axotd.jpg": (
                "https://matest.kz/upload/iblock/618/"
                "jrynmeif6iziza2djdiblxxcvg7axotd.jpg"
            ),
            "lg07obzcp11ix0cp5brlg8un1l7yr0r1.jpg": (
                "https://matest.kz/upload/iblock/1f3/"
                "lg07obzcp11ix0cp5brlg8un1l7yr0r1.jpg"
            ),
            "vbvzg5dqgo0sgv0cpeypz7ih8ww7ydyk.jpg": (
                "https://matest.kz/upload/iblock/682/"
                "vbvzg5dqgo0sgv0cpeypz7ih8ww7ydyk.jpg"
            ),
            "svcw7ahwekkg7d7tkn31lwjfhjpfbxlk.jpg": (
                "https://matest.kz/upload/iblock/4bb/"
                "svcw7ahwekkg7d7tkn31lwjfhjpfbxlk.jpg"
            ),
            "4ye94p4lpliyxzr14xaykfalrpqao32k.jpg": (
                "https://matest.kz/upload/iblock/b4e/"
                "4ye94p4lpliyxzr14xaykfalrpqao32k.jpg"
            ),
            "zkpr8y7lo3gd5nm5wvdjey9cbp8s0ixs.jpg": (
                "https://matest.kz/upload/iblock/ec2/"
                "zkpr8y7lo3gd5nm5wvdjey9cbp8s0ixs.jpg"
            ),
            "5px8rkkvf760oogyqlk5mm0a1blxpgrd.jpg": (
                "https://matest.kz/upload/iblock/142/"
                "5px8rkkvf760oogyqlk5mm0a1blxpgrd.jpg"
            ),
            "uslr6xhqf1umwmc4fvzlnx91jnuz41pa.jpg": (
                "https://matest.kz/upload/iblock/b17/"
                "uslr6xhqf1umwmc4fvzlnx91jnuz41pa.jpg"
            ),
            "0qki5asqbacuur76rwofeof71o8416sx.jpg": (
                "https://matest.kz/upload/iblock/223/"
                "0qki5asqbacuur76rwofeof71o8416sx.jpg"
            ),
            "m5odqocwtbr3drt02w9berryyr3vvk2k.jpg": (
                "https://matest.kz/upload/iblock/d0e/"
                "m5odqocwtbr3drt02w9berryyr3vvk2k.jpg"
            ),
            "sc63xizwi4gh1x0bva6xgjtfbm1hqz0d.jpg": (
                "https://matest.kz/upload/iblock/cf6/"
                "sc63xizwi4gh1x0bva6xgjtfbm1hqz0d.jpg"
            ),
            "0mgnp46j5q3hz0sd3ezebvl24ks3wi96.jpg": (
                "https://matest.kz/upload/iblock/0ed/"
                "0mgnp46j5q3hz0sd3ezebvl24ks3wi96.jpg"
            ),
            "48uozm91gu384yf11i3koutdp27i878h.jpg": (
                "https://matest.kz/upload/iblock/293/"
                "48uozm91gu384yf11i3koutdp27i878h.jpg"
            ),
            "j1hb4k92aiu5ii98jz4k3mn3urn8lp5k.jpg": (
                "https://matest.kz/upload/iblock/629/"
                "j1hb4k92aiu5ii98jz4k3mn3urn8lp5k.jpg"
            ),
            "66gaog7bfdofmb30zkkntxqa6lb32ivv.jpg": (
                "https://matest.kz/upload/iblock/40a/"
                "66gaog7bfdofmb30zkkntxqa6lb32ivv.jpg"
            ),
            "at7kjsf6x88v8og6pm2fg01if3th4xzt.jpg": (
                "https://matest.kz/upload/iblock/599/"
                "at7kjsf6x88v8og6pm2fg01if3th4xzt.jpg"
            ),
            "tqeh4vk80hypi1qttkzpm9dxxd6gnk92.jpg": (
                "https://matest.kz/upload/iblock/451/"
                "tqeh4vk80hypi1qttkzpm9dxxd6gnk92.jpg"
            ),
            "2kmc9bkpl3m417pdl45abmxuowh015u0.jpg": (
                "https://matest.kz/upload/iblock/bb5/"
                "2kmc9bkpl3m417pdl45abmxuowh015u0.jpg"
            ),
            "0fqg7iol23ooyufxqe3m1wzw2h1ys9og.jpg": (
                "https://matest.kz/upload/iblock/b6c/"
                "0fqg7iol23ooyufxqe3m1wzw2h1ys9og.jpg"
            ),
            "v0q0tfbe39q1oefaqhiimq7iyobqqeh8.jpg": (
                "https://matest.kz/upload/iblock/6a5/"
                "v0q0tfbe39q1oefaqhiimq7iyobqqeh8.jpg"
            ),
            "y6dohpo80c0r8loubvzrzfo4wr44zz20.jpg": (
                "https://matest.kz/upload/iblock/659/"
                "y6dohpo80c0r8loubvzrzfo4wr44zz20.jpg"
            ),
            "i78nkpzb392ea7b4doih3ktleawhayq3.jpg": (
                "https://matest.kz/upload/iblock/db0/"
                "i78nkpzb392ea7b4doih3ktleawhayq3.jpg"
            ),
            "r0nzp2rsxns9e167zjlqkj11xnxltnuo.jpg": (
                "https://matest.kz/upload/iblock/f3e/"
                "r0nzp2rsxns9e167zjlqkj11xnxltnuo.jpg"
            ),
            "ayz23y7tywd3mrbzx8c3m6ucjjh2pvrn.jpg": (
                "https://matest.kz/upload/iblock/69a/"
                "ayz23y7tywd3mrbzx8c3m6ucjjh2pvrn.jpg"
            ),
            "hrrok7xwyoo925t1q07tft2zr6a1rxjx.jpg": (
                "https://matest.kz/upload/iblock/ac4/"
                "hrrok7xwyoo925t1q07tft2zr6a1rxjx.jpg"
            ),
            "1am9u547oo4z1aqw93mt08exmlh8he0p.jpg": (
                "https://matest.kz/upload/iblock/ecc/"
                "1am9u547oo4z1aqw93mt08exmlh8he0p.jpg"
            ),
            "we2msh817g3yca0p4kcgft9jzb20n0gl.jpg": (
                "https://matest.kz/upload/iblock/75d/"
                "we2msh817g3yca0p4kcgft9jzb20n0gl.jpg"
            ),
            "51jzkzf9dce1iw6kzbmzs2i9bp28jw6i.jpg": (
                "https://matest.kz/upload/iblock/438/"
                "51jzkzf9dce1iw6kzbmzs2i9bp28jw6i.jpg"
            ),
            "kcj6fh01egcsmrcf1lgqiyij8g83b1ld.jpg": (
                "https://matest.kz/upload/iblock/e8b/"
                "kcj6fh01egcsmrcf1lgqiyij8g83b1ld.jpg"
            ),
            "0nfpa3a4c1labv3zvw5ty0a36z5468un.jpg": (
                "https://matest.kz/upload/iblock/774/"
                "0nfpa3a4c1labv3zvw5ty0a36z5468un.jpg"
            ),
            "100d7w23bebwcgbs9mraffsalo20ldrf.jpg": (
                "https://matest.kz/upload/iblock/d62/"
                "100d7w23bebwcgbs9mraffsalo20ldrf.jpg"
            ),
            "kzrnfwem3ziow719n7ktfhgaao2ifec0.jpg": (
                "https://matest.kz/upload/iblock/9b9/"
                "kzrnfwem3ziow719n7ktfhgaao2ifec0.jpg"
            ),
            "8klzsg2xgmgq5mzn9r9c5npx4tqra4ii.jpg": (
                "https://matest.kz/upload/iblock/d29/"
                "8klzsg2xgmgq5mzn9r9c5npx4tqra4ii.jpg"
            ),
        }
        logger.info("---")
        total = 0
        start = 0
        not_found: list[str] = []
        while True:

            product_ids = await product_bitrix_client.list(["id"], start=start)
            res = product_ids.result
            for re in res:

                ext_id = re.external_id
                image_service = product_bitrix_client.image_service
                prs = await image_service.get_pictures_by_product_id(ext_id)

                for pr in prs:
                    if link := image_dict.get(pr.name):
                        pr.supplier_image_url = link
                        pr.source = SourcesProductEnum.MATEST
                    else:
                        not_found.append(
                            f"{re.external_id}: not found *{pr.name}*"
                        )
                    try:
                        await product_image_repo.create_or_update(pr)
                    except Exception:
                        await product_client.import_from_bitrix(ext_id)
                        await product_image_repo.create_or_update(pr)
                total += 1
                # if total == 3:
                #     break
            try:
                start = int(product_ids.next)
            except Exception:
                start = 0
            if not start:
                break
        logger.info(f"{total}**********************************************")
        logger.info(
            f"{not_found}**********************************************"
        )
        # from schemas.enums import SourcesProductEnum
        # from schemas.product_image_schemas import ProductImageCreate
        # product_image_create = ProductImageCreate(
        #     external_id=3,
        #     name="test77777777777",
        #     product_id=801,
        #     source=SourcesProductEnum.MATEST,
        #     detail_url="https:",
        #     image_type="MORE_IMAGE",
        # )
        # await product_image_repo.create_or_update(product_image_create)
        # image = await product_image_repo.get(3)
        # logger.info(type(image))
        # from datetime import date
        # lead_ids = await lead_client.bitrix_client.get_lead_ids_for_period(
        #     date(2025, 10, 20), date(2026, 3, 4)
        # )
        # for lead_id in lead_ids:
        #     # logger.info(f"lead_id: {lead_id}")
        #     await lead_client.import_from_bitrix(entity_id=lead_id)
        # await lead_client.send_overdue_leads_notifications()
        # leads = await lead_client.repo.get_overdue_leads()
        # for lead, idle_time in leads:
        #     logger.info(
        #         f"Лид {lead.title} Ответственный {lead.assigned_user.name} "
        #         f"Стадия {lead.status_id} лежит без продвижения {idle_time}"
        #     )
        # result_ = ""
        # await deal_client.handle_deal(257)
        # for external_id in range(2001, 2148, 2):
        #     product_update = ProductUpdate(
        #         external_id=external_id, brend=FieldValue(value="93")
        #     )
        #     await product_bitrix_client.update(product_update)
        #     print(f"UPDATED {external_id}")
        # pr = await product_bitrix_client.image_service.
        # get_pictures_by_product_id(
        #     2155
        # )
        # logger.info(pr)
        # result_ = result[0].to_pydantic().model_dump_json()
        # result = await product_client.import_from_bitrix(2350)
        # result = await product_client.repo.get_by_id(
        #     "90909a41-8222-45b9-b9ed-d50e1a0cbd7b"
        # )
        # result_ = await result[0].to_pydantic()=======================")
        # await result.to_pydantic()
        # logger.info(f"{await result.to_pydantic()}====================")
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "external_id": f"{external_id}"},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "result": "result_.model_dump_json()",
        },
    )
